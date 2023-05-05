import logging

from asnake.client import ASnakeClient

logger = logging.getLogger(__name__)


class AsOperations:
    def __init__(self, client: ASnakeClient) -> None:
        """
        Create instance and import client as attribute.

        Args:
            client: A configured ASnakeClient.
        """
        self.client = client

    def get_record(self, uri: str) -> dict:
        """
        Retrieve an ArchivesSpace record.

        Args:
            uri: An ArchivesSpace record's Uniform Resource Identifier.
        """
        record = self.client.get(uri).json()
        logger.info("Retrieved record: %s", uri)
        return record

    def post_new_record(self, record_object: dict, endpoint: str) -> dict:
        """
        Create new ArchivesSpace record with POST of JSON data.

        Args:
            record_object: An ArchivesSpace record as a JSON object.
            endopoint: An endpoint for posting the specific type of ArchivesSpace record.
        """
        response = self.client.post(endpoint, json=record_object)
        logger.info(response.json())
        response.raise_for_status()
        return response.json()

    def update_record(self, record_object: dict) -> dict:
        """
        Update an ArchivesSpace record with POST of JSON data.

        Args:
            record_object: An ArchivesSpace record as a JSON object.
        """
        response = self.client.post(record_object["uri"], json=record_object)
        logger.info(response.json())
        response.raise_for_status()
        return response.json()
