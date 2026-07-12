from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository

import_jobs = db["import_jobs"]


class ImportJobRepository(BaseRepository):

    def __init__(self):
        super().__init__(import_jobs)

    def create_indexes(self):

        self.collection.create_index(
            [("job_number", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("bl_no", ASCENDING)]
        )

        self.collection.create_index(
            [("invoice_no", ASCENDING)]
        )

        self.collection.create_index(
            [("line_name", ASCENDING)]
        )

        self.collection.create_index(
            [("forwarder", ASCENDING)]
        )

    def find_by_job_number(self, job_number):

        return self.collection.find_one(
            {
                "job_number": job_number,
                "is_deleted": False,
            }
        )

    def find_by_name(self, name: str):
        return self.collection.find_one(
            {
                "customer_name": name,
                "is_deleted": False,
            }
        )
    def search(
        self,
        search="",
        skip=0,
        limit=20,
    ):

        query = {
            "is_deleted": False
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
                    "invoice_no": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "consignee_name": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "forwarder": {
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


import_job_repository = ImportJobRepository()