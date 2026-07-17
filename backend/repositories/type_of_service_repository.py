from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from backend.database.mongo import db


class TypeOfServiceRepository:
    def __init__(self):
        self.collection = db.type_of_services

    def create_indexes(self):
        self.collection.create_index(
            [("name", ASCENDING)],
            unique=True,
        )

    def get_all(self, search=None):
        query = {}

        if search:
            query["name"] = {
                "$regex": search,
                "$options": "i",
            }

        return list(
            self.collection.find(
                query,
                {"_id": 0},
            ).sort("name", ASCENDING)
        )

    def create(self, name):
        name = name.strip()

        try:
            self.collection.insert_one({"name": name})
        except DuplicateKeyError:
            raise ValueError("Type of Service already exists.")

        return {"name": name}

    def update(self, old_name, new_name):
        new_name = new_name.strip()

        try:
            result = self.collection.update_one(
                {"name": old_name},
                {"$set": {"name": new_name}},
            )
        except DuplicateKeyError:
            raise ValueError("Type of Service already exists.")

        if result.matched_count == 0:
            raise ValueError("Type of Service not found.")

        return {"name": new_name}

    def delete(self, name):
        result = self.collection.delete_one({"name": name})

        if result.deleted_count == 0:
            raise ValueError("Type of Service not found.")


type_of_service_repository = TypeOfServiceRepository()