import csv
import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from time import perf_counter

import click
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
@click.option("--modify_data", is_flag=True)
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
