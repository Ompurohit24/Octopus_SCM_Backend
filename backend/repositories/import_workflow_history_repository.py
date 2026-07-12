from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository

collection = db["import_workflow_history"]


class ImportWorkflowHistoryRepository(BaseRepository):

    def __init__(self):
        super().__init__(collection)

    def create_indexes(self):

        self.collection.create_index(
            [("workflow_id", ASCENDING)]
        )

        self.collection.create_index(
            [("job_id", ASCENDING)]
        )

        self.collection.create_index(
            [("job_number", ASCENDING)]
        )

        self.collection.create_index(
            [("created_at", ASCENDING)]
        )

    def get_history(
        self,
        workflow_id: str,
    ):

        return self.list(
            query={
                "workflow_id": workflow_id,
            },
            sort_field="created_at",
        )


import_workflow_history_repository = ImportWorkflowHistoryRepository()