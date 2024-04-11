import csv
import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from time import perf_counter

import click
from asnake.client import ASnakeClient  # type: ignore[import-untyped]

from top_containers.models import AsOperations
from top_containers.records import create_instance, create_top_container

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
@click.option(
    "--metadata_csv",
    required=True,
    prompt="Enter the name to the metadata CSV (e.g. 'metadata.csv'): ",
)
@click.option("--modify_data", is_flag=True)
def main(
    as_instance: str,
    directory: str,
    repository_id: str,
    metadata_csv: str,
    modify_data: bool,  # noqa: FBT001
) -> None:
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
    with open(f"{directory}/{metadata_csv}", encoding="utf-8") as input_file, open(
        f"{directory}/{current_date.strftime('%Y-%m-%d_%H.%M.%S')}.csv",
        "w",
        encoding="utf-8",
    ) as output_file:
        output_csv = csv.DictWriter(output_file, fieldnames=["uri", "title", "data"])
        output_csv.writeheader()
        for metadata in csv.DictReader(input_file):
            top_container = create_top_container(
                metadata, current_date.strftime("%Y-%m-%d")
            )
            top_container_uri = "Dry run, top container URI not created"
            if modify_data:
                top_container_post_response = as_ops.post_new_record(
                    top_container,
                    f"repositories/{repository_id}/top_containers",
                )
                top_container_uri = top_container_post_response["uri"]
            output_csv.writerow(
                {"uri": top_container_uri, "title": "NA", "data": top_container}
            )

            accession_record = as_ops.get_record(metadata["accession_uri"])
            instance = create_instance(metadata["instance_type"], top_container_uri)
            accession_record["instances"].append(instance)
            if modify_data:
                as_ops.update_record(accession_record)
            else:
                logger.info("Dry run, record '%s' not updated", accession_record["uri"])
            output_csv.writerow(
                {
                    "uri": accession_record["uri"],
                    "title": accession_record["title"],
                    "data": instance,
                }
            )
    logger.info(
        "Total time to complete process: %s",
        timedelta(seconds=perf_counter() - start_time),
    )
