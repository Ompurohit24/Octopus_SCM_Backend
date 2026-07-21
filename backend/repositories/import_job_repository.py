from pymongo import ASCENDING
from bson import ObjectId
from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository
from datetime import datetime
import_jobs = db["import_jobs"]


class ImportJobRepository(BaseRepository):

    def __init__(self):
        super().__init__(import_jobs)

    def create_indexes(self):
        # -------------------------------------------------
        # PERMANENT SYSTEM IDENTIFIER
        #
        # IMP-xxxxx must NEVER be reused.
        # -------------------------------------------------

        self.collection.create_index(
            [("job_number", ASCENDING)],
        )

        # -------------------------------------------------
        # BL NUMBER
        #
        # Duplicate validation is handled by:
        # find_by_bl_no()
        #
        # which already checks:
        # is_deleted = False
        #
        # Therefore a BL from a deleted Job can be reused.
        # -------------------------------------------------

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

        self.collection.create_index(
            [("is_deleted", ASCENDING)]
        )

    def find_by_job_number(self, job_number):

        return self.collection.find_one(
            {
                "job_number": job_number,
                "is_deleted": False,
            }
        )

    def find_by_bl_no(self, bl_no: str):
        return self.collection.find_one(
            {
                "bl_no": bl_no,
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

    def is_line_name_in_use(self, name: str):
        return self.collection.find_one(
            {
                "line_name": name,
                "is_deleted": False,
            }
        ) is not None
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

    def update_by_id(
            self,
            job_id: str,
            data: dict,
    ):
        self.collection.update_one(
            {
                "_id": ObjectId(job_id),
                "is_deleted": False,
            },
            {
                "$set": data,
            },
        )

    def soft_delete_by_id(
            self,
            job_id: str,
            session=None,
    ):
        return self.collection.update_one(
            {
                "_id": ObjectId(job_id),
                "is_deleted": False,
            },
            {
                "$set": {
                    "is_active": False,
                    "is_deleted": True,
                    "updated_at": datetime.utcnow(),
                }
            },
            session=session,
        )

    def find_active_by_customer(
            self,
            customer_name: str,
    ):
        return self.collection.find_one(
            {
                "is_deleted": False,
                "$or": [
                    {
                        "forwarder": customer_name,
                    },
                    {
                        "forwarder_name": customer_name,
                    },
                ],
            }
        )

import_job_repository = ImportJobRepository()