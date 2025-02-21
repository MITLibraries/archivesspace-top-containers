import csv
import itertools
import logging
import os
import sys
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from time import perf_counter

import click
import pandas as pd
from asnake.client import ASnakeClient  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option(
    "--as_instance",
    required=True,
    prompt="Select the ArchivesSpace instance to use, either 'dev' or 'prod': ",
    type=click.Choice(["dev", "prod"]),
)
@click.option("--modify-data", is_flag=True, default=True)
def main(ctx: click.Context, as_instance: str, modify_data: bool) -> None:  # noqa: FBT001
    ctx.ensure_object(dict)
    ctx.obj["start_time"] = perf_counter()
    ctx.obj["modify_data"] = modify_data
    ctx.obj["as_instance"] = as_instance

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s.%(funcName)s(): %(message)s",
        level=logging.INFO,
    )
    as_url = os.environ["PROD_URL"] if as_instance == "prod" else os.environ["DEV_URL"]
    as_user = os.environ["PROD_USER"] if as_instance == "prod" else os.environ["DEV_USER"]
    as_password = (
        os.environ["PROD_PASSWORD"]
        if as_instance == "prod"
        else os.environ["DEV_PASSWORD"]
    )
    logger.info(
        "Authenticating to '%s' (%s) as '%s' with modify_data set to '%s'",
        as_instance,
        as_url,
        as_user,
        modify_data,
    )

    aspace_client = ASnakeClient(baseurl=as_url, username=as_user, password=as_password)
    aspace_client.authorize()

    ctx.obj["as_url"] = as_url
    ctx.obj["aspace_client"] = aspace_client


@main.result_callback()
@click.pass_context
def post_main_group_subcommand(
    ctx: click.Context,
    *_args: tuple,
    **_kwargs: dict,
) -> None:
    """Callback for any work to perform after a main sub-command completes."""
    logger.info("Application exiting")
    logger.info(
        "Total time elapsed: %s",
        str(
            timedelta(seconds=perf_counter() - ctx.obj["start_time"]),
        ),
    )


@main.command()
@click.pass_context
def agent_report(ctx: click.Context) -> None:
    aspace_client = ctx.obj["aspace_client"]

    logger.info("Creating report on ArchivesSpace agents with no linked records")
    agent_types = ["people", "corporate_entities", "software", "families"]

    agents_with_no_linked_records = []
    count = 0
    for agent_type in agent_types:
        agent_ids = aspace_client.get(f"agents/{agent_type}?all_ids=true").json()
        logger.info(f"Scanning all {len(agent_ids)} '{agent_type}' agents")
        for agent_id in agent_ids:
            count += 1

            if count % 500 == 0:
                logger.info(f"Scanned {count}/{len(agent_ids)} agents")

            agent = aspace_client.get(f"agents/{agent_type}/{agent_id}").json()
            if not agent["is_linked_to_published_record"]:
                agents_with_no_linked_records.append(
                    {
                        "agent_ids": agent_id,
                        "agent_name": agent["display_name"]["sort_name"],
                        "agent_type": agent_type,
                        "agent_uri": agent["uri"],
                    }
                )

    # write to CSV file
    logger.info(
        f"Found {len(agents_with_no_linked_records)} agents with no linked records"
    )
    report_filename = "agents_with_no_linked_records.csv"
    with open(report_filename, "w") as csvfile:
        field_names = ["agent_ids", "agent_name", "agent_type", "agent_uri"]
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(agents_with_no_linked_records)
    logger.info(f"Created report: {report_filename}")


@main.command()
@click.pass_context
def agreement_signed_event_records(ctx: click.Context):
    modify_data = ctx.obj["modify_data"]
    as_instance = ctx.obj["as_instance"]
    as_url = ctx.obj["as_url"]
    aspace_client = ctx.obj["aspace_client"]

    current_date = datetime.now(tz=UTC)

    if modify_data:
        proceed = input(
            f"Data will be modified on '{as_instance}' ({as_url}). Enter y to proceed: "
        )
        if proceed != "y":
            logger.info(
                "Halting process based on user input '%s' which is not 'y'", proceed
            )
            sys.exit()

    with open(f"deleted-{current_date}.csv", "w", encoding="utf-8") as output_file:
        output_csv = csv.writer(output_file)
        output_csv.writerow(["event_response"])
        endpoint = "repositories/2/events"
        for identifier in aspace_client.get(f"{endpoint}?all_ids=true").json():
            event = aspace_client.client.get(f"{endpoint}/{identifier}").json()
            if event["event_type"] == "agreement_signed":
                output_csv.writerow([event["uri"]])

    ead_id_uri = {}
    endpoint = "repositories/2/resources"
    for identifier in aspace_client.get(f"{endpoint}?all_ids=true").json():
        resource = aspace_client.get(f"{endpoint}/{identifier}").json()
        if not resource.get("ead_id"):
            ead_id = f"{resource["id_0"]}-{resource["id_1"]}"
            ead_id_uri[ead_id] = resource["uri"]
        else:
            ead_id = resource["ead_id"]
            ead_id_uri[ead_id] = resource["uri"]

    with open("Agreement-Signed-events.csv", encoding="utf-8") as input_file, open(
        "Agreement-Signed-events-results.csv",
        "w",
        encoding="utf-8",
    ) as output_file:
        output_csv = csv.DictWriter(  # type: ignore[assignment]
            output_file,
            fieldnames=["event_uri", "Identifier", "resource_uri", "Gift Agreement"],
        )
        output_csv.writeheader()  # type: ignore[attr-defined]
        for row in csv.DictReader(input_file):
            gift_agreement = row["Gift Agreement"]
            if gift_agreement != "N/A":
                event = {}
                event["event_type"] = "agreement_signed"
                event["linked_records"] = [
                    {"role": "source", "ref": ead_id_uri[row["Identifier"]]},
                ]
                event["linked_agents"] = [
                    {"role": "authorizer", "ref": "/agents/corporate_entities/1"}
                ]
                date = {
                    "date_type": "single",
                    "label": "event",
                    "jsonmodel_type": "date",
                }

                if gift_agreement == "Pass":
                    date["expression"] = "date not examined"
                    event["outcome"] = "pass"
                elif gift_agreement == "Partial Pass":
                    date["expression"] = "date not examined"
                    event["outcome"] = "partial pass"
                elif gift_agreement == "Fail":
                    date["begin"] = "2024"
                    event["outcome"] = "fail"
                event["date"] = date
                output_csv.writerow(
                    {
                        "Identifier": row["Identifier"],
                        "Gift Agreement": row["Gift Agreement"],
                        "resource_uri": ead_id_uri[row["Identifier"]],
                    }
                )


@main.command()
@click.pass_context
def retrieve_archival_objects_with_unpublished_access_notes(ctx: click.Context):
    modify_data = ctx.obj["modify_data"]
    as_instance = ctx.obj["as_instance"]
    as_url = ctx.obj["as_url"]
    aspace_client = ctx.obj["aspace_client"]

    if modify_data:
        proceed = input(
            f"Data will be modified on '{as_instance}' ({as_url}). Enter y to proceed: "
        )
        if proceed != "y":
            logger.info(
                "Halting process based on user input '%s' which is not 'y'", proceed
            )
            sys.exit()

    endpoint = "repositories/2/archival_objects"
    archival_object_ids = aspace_client.get(f"{endpoint}?all_ids=true").json()
    archival_object_ids.sort()  # sort AO ids in ascending order

    chunks = []
    chunk_size = 50_000
    for i in range(0, len(archival_object_ids), chunk_size):
        chunks.append(archival_object_ids[i : i + chunk_size])
    for chunk in chunks:
        print(len(chunk))
    chunk_number = 4
    archival_objects_to_update = []
    for ao_count, identifier in enumerate(chunks[chunk_number]):
        if ao_count % 2000 == 0:
            print(ao_count)
        archival_object_uri = f"{endpoint}/{identifier}"
        archival_object = aspace_client.get(archival_object_uri).json()
        update_archival_object = False
        for note in archival_object["notes"]:
            if note.get("type") == "accessrestrict":
                if not note["publish"]:
                    update_archival_object = True
                    note["publish"] = True
                for subnote in [
                    subnote
                    for subnote in note.get("subnotes", [])
                    if not subnote.get("publish")
                ]:
                    update_archival_object = True
                    subnote["publish"] = True
        if update_archival_object:
            archival_objects_to_update.append(archival_object_uri)
            # as_ops.update_record(f"{endpoint}/{identifier}", archival_object)
    print(archival_objects_to_update)
    print(len(archival_objects_to_update))


@main.command()
@click.pass_context
@click.option("-f", "--archival-objects-filename", required=True, type=str)
@click.option("--last-batch-num", required=True, type=int)
@click.option("--batch-size", required=False, type=int, default=10)
@click.option("--max-batches", required=True, type=int, default=1)
def publish_archival_objects_with_unpublished_access_notes(
    ctx: click.Context,
    archival_objects_filename: str,
    last_batch_num: int,
    batch_size: int = 50,
    max_batches: int = 5,
):
    modify_data = ctx.obj["modify_data"]
    as_instance = ctx.obj["as_instance"]
    as_url = ctx.obj["as_url"]
    aspace_client = ctx.obj["aspace_client"]

    if modify_data:
        proceed = input(
            f"Data will be modified on '{as_instance}' ({as_url}). Enter y to proceed: "
        )
        if proceed != "y":
            logger.info(
                "Halting process based on user input '%s' which is not 'y'", proceed
            )
            sys.exit()

    archival_objects_df = pd.read_csv(archival_objects_filename)
    archival_objects_dict = archival_objects_df.to_dict(orient="records")

    logger.info(
        f"Identified {len(archival_objects_dict)} Archival Objects with unpublished access notes"
    )

    archival_objects_processed = []

    batch_count = 0
    for batch_num, batch in enumerate(
        itertools.batched(archival_objects_dict, batch_size)
    ):
        if batch_num < last_batch_num:
            logger.info(f"Skipping batch {batch_num} (n={len(batch)})")
            continue

        if batch_count >= max_batches:
            logger.info(f"Processed max number of batches {max_batches}")
            break

        batch_count += 1

        for archival_object_record in batch:
            archival_object_uri = archival_object_record["archival_object_uris"]

            if archival_object_record.get("updated"):
                logger.info(
                    f"Archival Object with uri: {archival_object_uri} already updated. Skipping"
                )
                archival_objects_processed.append(archival_object_record)
                continue

            # actual archival object
            archival_object = aspace_client.get(archival_object_uri).json()

            archival_object_is_updated = False
            for note in archival_object["notes"]:
                if note.get("type") == "accessrestrict":
                    if note["publish"] is False:
                        note["publish"] = True
                        archival_object_is_updated = True

                    for subnote in note.get("subnotes", []):
                        if subnote.get("publish") is False:
                            subnote["publish"] = True
                            archival_object_is_updated = True

            # populate details for archival object
            archival_object_record["resource_uri"] = archival_object["resource"]["ref"]
            archival_object_record["display_string"] = archival_object["display_string"]

            if archival_object_is_updated:
                archival_objects_processed.append(archival_object_record)
                response = aspace_client.post(archival_object_uri, json=archival_object)
                response.raise_for_status()
                logger.info(f"POST status code: {response.status_code}")
                logger.debug(f"Updated Archival Object with uri: {archival_object_uri}")
                archival_object_record["updated"] = True
            else:
                archival_object_record["updated"] = False
                archival_objects_processed.append(archival_object_record)
                logger.debug(
                    f"No changes to Archival Object with uri: {archival_object_uri}"
                )
        logger.info(f"Processed batch {batch_num}")

    # update CSV with processed archival objects
    archival_objects_processed_df = pd.DataFrame.from_dict(
        archival_objects_processed, orient="columns"
    )
    report_filename_new = f"archival_objects_published_{uuid.uuid4()}.csv"
    logger.info(
        f"Created new report with published Archival Objects: {report_filename_new}"
    )
    archival_objects_processed_df.to_csv(report_filename_new, index=False)
