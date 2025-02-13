import csv
import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from time import perf_counter

import click
from asnake.client import ASnakeClient  # type: ignore[import-untyped]

from top_containers.models import AsOperations

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--as_instance",
    required=True,
    prompt="Select the ArchivesSpace instance to use, either 'dev' or 'prod': ",
    type=click.Choice(["dev", "prod"]),
)
@click.option(
    "--directory",
    required=True,
    default="data",
)
@click.option(
    "--repository_id",
    required=True,
    default="2",
)
@click.option("--modify_data", is_flag=True)
def main(as_instance: str, modify_data: bool) -> None:  # noqa: FBT001
    start_time = perf_counter()
    current_date = datetime.now(tz=UTC)
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

    if modify_data:
        proceed = input(
            f"Data will be modified on '{as_instance}' ({as_url}). Enter y to proceed: "
        )
        if proceed != "y":
            logger.info(
                "Halting process based on user input '%s' which is not 'y'", proceed
            )
            sys.exit()

    as_ops = AsOperations(
        ASnakeClient(baseurl=as_url, username=as_user, password=as_password)
    )
    with open(f"deleted-{current_date}.csv", "w", encoding="utf-8") as output_file:
        output_csv = csv.writer(output_file)
        output_csv.writerow(["event_response"])
        endpoint = "repositories/2/events"
        for identifier in as_ops.client.get(f"{endpoint}?all_ids=true").json():
            event = as_ops.client.get(f"{endpoint}/{identifier}").json()
            if event["event_type"] == "agreement_signed":
                output_csv.writerow([event["uri"]])

    ead_id_uri = {}
    endpoint = "repositories/2/resources"
    for identifier in as_ops.client.get(f"{endpoint}?all_ids=true").json():
        resource = as_ops.client.get(f"{endpoint}/{identifier}").json()
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

    logger.info(
        "Total time to complete process: %s",
        timedelta(seconds=perf_counter() - start_time),
    )
