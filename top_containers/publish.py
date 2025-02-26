import os
from concurrent.futures import ThreadPoolExecutor

from asnake.client import ASnakeClient  # type: ignore[import-untyped]

ASPACE_URL = os.getenv("DEV_URL")
ASPACE_USER = os.getenv("DEV_USER")
ASPACE_PASSWORD = os.getenv("DEV_PASSWORD")

AO_ENDPOINT = "repositories/2/archival_objects"

aspace_client = ASnakeClient(
    baseurl=ASPACE_URL, username=ASPACE_USER, password=ASPACE_PASSWORD
)
archival_object_ids = aspace_client.get(f"{AO_ENDPOINT}?all_ids=true").json()
archival_object_ids.sort()

print(f"Found {len(archival_object_ids)} archival objects.")


def get_ao(ao_id: str):
    ao = aspace_client.get(f"{AO_ENDPOINT}/{ao_id}").json()
    return ao


def update_ao():
    ao = get_ao()
    ao_needs_updating = False

    # check if "Conditions Governing Access" has publish=False
    for note in ao["notes"]:
        if note.get("type") == "accessrestrict":
            if note["publish"] is False:
                note["publish"] = True

                # flag that AO needs to be updated
                ao_needs_updating = True

                for subnote in note.get("subnotes"):
                    if subnote["publish"] is False:
                        subnote["publish"] = True

    if ao_needs_updating:
        print(f"Updating notes for Archival Object '{ao["uri"]}'")
        aspace_client.post(ao["uri"], json=ao)


def update_ao_bulk():
    pass
