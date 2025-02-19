# ruff: noqa: ERA001, PERF401, T201
import logging
import os
import sys
from datetime import timedelta
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
@click.option("--modify_data", is_flag=True)
def main(
    as_instance: str,
    modify_data: bool,  # noqa: FBT001
) -> None:
    start_time = perf_counter()
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
    endpoint = "repositories/2/archival_objects"
    archival_object_ids = as_ops.client.get(f"{endpoint}?all_ids=true").json()
    archival_object_ids.sort()
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
        archival_object = as_ops.client.get(archival_object_uri).json()
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

    logger.info(
        "Total time to complete process: %s",
        timedelta(seconds=perf_counter() - start_time),
    )
