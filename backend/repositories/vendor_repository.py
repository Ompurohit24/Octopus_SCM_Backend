from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository

vendors = db["vendors"]


class VendorRepository(BaseRepository):

    def __init__(self):
        super().__init__(vendors)

    def create_indexes(self):

        self.collection.create_index(
            [("vendor_code", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("vendor_name", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("email", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("phone", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("gstin", ASCENDING)],
            unique=True,
        )

        self.collection.create_index(
            [("pan", ASCENDING)],
            unique=True,
        )

    def find_by_code(self, code):

        return self.collection.find_one(
            {
                "vendor_code": code,
                "is_deleted": False,
            }
        )

    def find_by_name(self, name):

        return self.collection.find_one(
            {
                "vendor_name": name,
                "is_deleted": False,
            }
        )

    def find_one(self, query):

        return self.collection.find_one(query)

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
                    "vendor_code": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "vendor_name": {
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
                {
                    "phone": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
            ]

        return self.list(
            query=query,
            skip=skip,
            limit=limit,
            sort_field="vendor_name",
        )


vendor_repository = VendorRepository()