def create_instance(instance_type: str, top_container_uri: str) -> dict:
    """
    Create an ArchivesSpace instance object for attaching to a record.

    Args:
        instance_type: The type of the instance.
        top_container_uri: The URI of the top container to link
        to the instance.
    """
    return {
        "instance_type": instance_type,
        "sub_container": {
            "top_container": {"ref": top_container_uri},
        },
    }


def create_top_container(metadata: dict, start_date: str) -> dict:
    """
    Create an ArchivesSpace top container object from a metadata dict and a date.

    Metadata dict must have the following keys:
        container_type
        indicator
        location_uri

    Args:
        metadata: A dict of metadata for the top container.
        start_date: The start date for the top container.
    """
    return {
        "type": metadata["container_type"],
        "indicator": metadata["indicator"],
        "container_locations": [
            {
                "jsonmodel_type": "container_location",
                "ref": metadata["location_uri"],
                "status": "current",
                "start_date": start_date,
            }
        ],
    }
