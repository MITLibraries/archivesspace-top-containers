import csv

import pandas as pd

from publish_ao_notes_full_prod import archival_object_uris


def convert_to_csv(archival_object_uris: list):

    print(f"Found {len(archival_object_uris)} Archival Objects that need publishing")

    header = [
        "archival_object_id",
        "archival_object_uris",
        "resource_uri",
        "display_string",
        "updated",
    ]
    report_filename = "archival_objects_with_unpublished_access_notes.csv"

    with open(report_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

        for archival_object_uri in archival_object_uris:
            archival_object_id = archival_object_uri.split("/")[-1]
            writer.writerow([archival_object_id, archival_object_uri, "", "", False])


if __name__ == "__main__":
    convert_to_csv(archival_object_uris)
