from datetime import datetime

from bson import ObjectId
from pymongo import ASCENDING


class BaseRepository:

    def __init__(self, collection):
        self.collection = collection

    def create(self, document):
        return self.collection.insert_one(document)

    def find_by_id(self, document_id):
        return self.collection.find_one({
            "_id": ObjectId(document_id),
            "is_deleted": False
        })

    def list(
        self,
        query=None,
        skip=0,
        limit=20,
        sort_field="created_at",
        sort_order=ASCENDING,
    ):

        if query is None:
            query = {"is_deleted": False}

        return list(
            self.collection.find(query)
            .sort(sort_field, sort_order)
            .skip(skip)
            .limit(limit)
        )

    def count(self, query=None):

        if query is None:
            query = {"is_deleted": False}

        return self.collection.count_documents(query)

    def update(self, document_id, data):

        data["updated_at"] = datetime.utcnow()

        return self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": data},
        )

    def soft_delete(self, document_id):

        return self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "is_deleted": True,
                    "is_active": False,
                    "updated_at": datetime.utcnow(),
                }
            },
        )