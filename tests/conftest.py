import pytest
import requests_mock
from asnake.client import ASnakeClient
from click.testing import CliRunner

from top_containers.models import AsOperations


@pytest.fixture
def as_ops():
    client = ASnakeClient(
        baseurl="mock://example.com", username="test", password="test"  # noqa: S106
    )
    return AsOperations(client)


@pytest.fixture(autouse=True)
def mock_archivesspace():
    with requests_mock.Mocker() as mock:
        accession_json = {
            "title": "Accession title",
            "uri": "/repositories/0/accessions/000",
            "instances": [
                {
                    "lock_version": 0,
                    "instance_type": "mixed_materials",
                    "jsonmodel_type": "instance",
                    "sub_container": {
                        "lock_version": 0,
                        "jsonmodel_type": "sub_container",
                        "top_container": {"ref": "/repositories/0/top_containers/000"},
                    },
                },
            ],
        }
        mock.get("/repositories/0/accessions/000", json=accession_json)
        mock.post("/repositories/0/accessions/000", json={"status": "Updated"})
        top_container_post_json = {
            "status": "Created",
            "uri": "/repositories/0/top_containers/001",
        }
        mock.post("/repositories/0/top_containers", json=top_container_post_json)
        yield mock


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("DEV_USER", "user")
    monkeypatch.setenv("DEV_PASSWORD", "password")
    monkeypatch.setenv("DEV_URL", "mock://example-dev.com")
    monkeypatch.setenv("PROD_USER", "user")
    monkeypatch.setenv("PROD_PASSWORD", "password")
    monkeypatch.setenv("PROD_URL", "mock://example-prod.com")


@pytest.fixture
def working_directory(tmp_path):
    directory = tmp_path / "data"
    directory.mkdir()
    metadata_csv = directory / "test_metadata.csv"
    with open("tests/fixtures/test_metadata.csv", encoding="utf-8") as csv_file:
        metadata_csv.write_text(csv_file.read())
    return f"{directory}/"
