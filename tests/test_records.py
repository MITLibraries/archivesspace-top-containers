from top_containers.records import create_instance, create_top_container


def test_create_instance():
    assert create_instance("mixed_materials", "repositories/0/top_containers/000") == {
        "instance_type": "mixed_materials",
        "sub_container": {"top_container": {"ref": "repositories/0/top_containers/000"}},
    }


def test_create_top_container():
    metadata = {
        "container_type": "DigitalStorage",
        "indicator": "abcd1234",
        "location_uri": "/locations/000",
    }
    assert create_top_container(metadata, "2023-01-01") == {
        "type": "DigitalStorage",
        "indicator": "abcd1234",
        "container_locations": [
            {
                "jsonmodel_type": "container_location",
                "ref": "/locations/000",
                "status": "current",
                "start_date": "2023-01-01",
            }
        ],
    }
