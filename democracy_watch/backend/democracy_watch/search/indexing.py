import os
from enum import Enum

import meilisearch
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class TaskSelection(Enum):
    INDEX = "index"
    SEARCH = "search"


class MeilisearchApiKeySelection(Enum):
    INDEX = "ADMIN_KEY"
    SEARCH = "MEILISEARCH_URL"


task = TaskSelection.INDEX


class DossierData(BaseModel):
    uid: str
    procedure: str
    status: str
    titre: str
    date_creation: str
    date_update: str
    date_depot: str
    date_denouement: str


class ArticleData(BaseModel):
    pass


class AmendementsData(BaseModel):
    texte: str
    dispositif: str
    expose_sommaire: str
    date_creation: str
    auteur: str


class MeilisearchManager:
    def __init__(self, task: TaskSelection):
        if task == TaskSelection.INDEX:
            self.client = meilisearch.Client(
                os.environ.get("MEILISEARCH_URL", ""),
                os.environ.get(MeilisearchApiKeySelection.INDEX.value),
            )
        else:
            self.client = meilisearch.Client(
                os.environ.get("MEILISEARCH_URL", ""),
                os.environ.get(MeilisearchApiKeySelection.SEARCH.value),
            )

    def get_status(self):
        """
        Function that describe the stauts of the loaded client Meilisearch.
        Arguments:
            None

        Returns:
            (json): Status of the client

        """
        return self.client.get_all_stats()

    def create_index_dossiers(self, data):
        pass

    def create_index_articles(self, data):
        pass

    def create_index_amendements(self, data):
        pass


if __name__ == "__main__":
    task = TaskSelection.INDEX
    manager = MeilisearchManager(task)
    print(manager.get_status())
