from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository

import_workflows = db["import_workflows"]

from datetime import datetime
class ImportWorkflowRepository(BaseRepository):

    def __init__(self):
        super().__init__(import_workflows)

    def create_indexes(self):

        self.collection.create_index(
            [("job_id", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("job_number", ASCENDING)]
        )

        self.collection.create_index(
            [("current_stage", ASCENDING)]
        )

        self.collection.create_index(
            [("is_deleted", ASCENDING)]
        )

    def find_by_job_id(self, job_id: str):

        return self.collection.find_one(
            {
                "job_id": job_id,
                "is_deleted": False,
            }
        )

    def find_by_job_number(self, job_number: str):

        return self.collection.find_one(
            {
                "job_number": job_number,
                "is_deleted": False,
            }
        )

    def search_jobs(
        self,
        search: str = "",
        skip: int = 0,
        limit: int = 20,
    ):

        query = {
            "is_deleted": False,
        }

        if search:

            query["$or"] = [
                {
                    "job_number": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "bl_no": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "party_name": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "be_no": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
            ]

        return self.list(
            query=query,
            skip=skip,
            limit=limit,
            sort_field="job_number",
        )

    def update_stage(
        self,
        job_id: str,
        stage: str,
        data: dict,
    ):

        data["current_stage"] = stage

        self.collection.update_one(
            {
                "job_id": job_id,
                "is_deleted": False,
            },
            {
                "$set": data,
            },
        )


    def soft_delete_by_job_id(
            self,
            job_id: str,
            session=None,
    ):
        now = datetime.utcnow()

        return self.collection.update_many(
            {
                "job_id": job_id,
                "is_deleted": {
                    "$ne": True,
                },
            },
            {
                "$set": {
                    "is_active": False,
                    "is_deleted": True,
                    "updated_at": now,
                }
            },
            session=session,
        )

import_workflow_repository = (
    ImportWorkflowRepository()
)