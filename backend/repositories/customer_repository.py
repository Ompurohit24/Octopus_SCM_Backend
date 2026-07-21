from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository


customers = db["customers"]


class CustomerRepository(BaseRepository):

    def __init__(self):
        super().__init__(customers)

    def create_indexes(self):
        # -------------------------------------------------
        # PERMANENT SYSTEM IDENTIFIER
        #
        # Customer Code must always remain unique.
        # -------------------------------------------------

        self.collection.create_index(
            [("customer_code", ASCENDING)],
            unique=True,
            name="customer_code_unique",
        )

        # -------------------------------------------------
        # SEARCH INDEXES ONLY
        #
        # Duplicate values are allowed for all
        # Customer business fields.
        # -------------------------------------------------

        self.collection.create_index(
            [("customer_name", ASCENDING)],
            name="customer_name_search",
        )

        self.collection.create_index(
            [("email", ASCENDING)],
            name="customer_email_search",
        )

        self.collection.create_index(
            [("phone", ASCENDING)],
            name="customer_phone_search",
        )

        self.collection.create_index(
            [("gstin", ASCENDING)],
            name="customer_gstin_search",
        )

        self.collection.create_index(
            [("pan", ASCENDING)],
            name="customer_pan_search",
        )

        self.collection.create_index(
            [("tan", ASCENDING)],
            name="customer_tan_search",
        )

    def find_by_code(self, code):

        return self.collection.find_one(
            {
                "customer_code": code,
                "is_deleted": False,
            }
        )

    def find_by_name(self, name):

        return self.collection.find_one(
            {
                "customer_name": name,
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
            "is_deleted": False
        }

        if search:

            query["$or"] = [
                {
                    "customer_code": {
                        "$regex": search,
                        "$options": "i",
                    }
                },
                {
                    "customer_name": {
                        "$regex": search,
                        "$options": "i",
                    }
                },

                # MongoDB regex matching works against
                # both string email values and arrays.
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
            sort_field="customer_name",
        )


customer_repository = CustomerRepository()