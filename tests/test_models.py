def test_as_ops_get_record(as_ops):
    response = as_ops.get_record("/repositories/0/accessions/000")
    assert response == {
        "title": "Accession title",
        "uri": "/repositories/0/accessions/000",
        "instances": [
            {
                "instance_type": "mixed_materials",
                "jsonmodel_type": "instance",
                "lock_version": 0,
                "sub_container": {
                    "jsonmodel_type": "sub_container",
                    "lock_version": 0,
                    "top_container": {"ref": "/repositories/0/top_containers/000"},
                },
            }
        ],
    }


def test_as_ops_post_new_record(as_ops):
    record_object = {"title": "Test title"}
    response = as_ops.post_new_record(record_object, "/repositories/0/top_containers")
    assert response == {
        "status": "Created",
        "uri": "/repositories/0/top_containers/001",
    }


def test_as_ops_update_record(as_ops):
    record_object = {"uri": "/repositories/0/accessions/000"}
    response = as_ops.update_record(record_object)
    assert response == {
        "status": "Updated",
    }
