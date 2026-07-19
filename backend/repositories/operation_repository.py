from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository


pub_operations = db["pub_operations"]
import_operations = db["import_operations"]


class OperationRepository(BaseRepository):

    def create_indexes(self):
        self.collection.create_index(
            [("email", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("mobile_number", ASCENDING)],
            unique=True,
        )

    def find_duplicate(
        self,
        *,
        email: str,
        mobile_number: str,
        exclude_id: str | None = None,
    ):
        checks = {
            "email": email,
            "mobile_number": mobile_number,
        }

        for field, value in checks.items():
            query = {
                field: value,
                "is_deleted": False,
            }

            if exclude_id:
                query["_id"] = {
                    "$ne": self.to_object_id(exclude_id)
                }

            if self.collection.find_one(query):
                return field

        return None

    def search(
        self,
        search="",
        skip=0,
        limit=20,
    ):
        query = {
            "is_deleted": False,
        }

        if search:
            query["$or"] = [
                {
                    "name": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "mobile_number": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "email": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
            ]

        return self.list(
            query=query,
            skip=skip,
            limit=limit,
            sort_field="name",
        )


pub_operation_repository = OperationRepository(
    pub_operations
)

import_operation_repository = OperationRepository(
    import_operations
)