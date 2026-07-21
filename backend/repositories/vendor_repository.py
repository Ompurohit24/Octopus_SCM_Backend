from pymongo import ASCENDING
import re
from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository
from bson import ObjectId


vendors = db["vendors"]


class VendorRepository(BaseRepository):

    def __init__(self):
        super().__init__(vendors)

    def get_next_code(self):
        last_vendor = self.collection.find_one(
            {"vendor_code": {"$regex": r"^VEN-\d+$"}},
            sort=[("vendor_code", -1)],
        )

        if not last_vendor:
            return "VEN-0001"

        last_code = last_vendor.get("vendor_code", "VEN-0000")

        try:
            last_number = int(last_code.split("-")[1])
        except (IndexError, ValueError):
            last_number = 0

        return f"VEN-{last_number + 1:04d}"

    def create_indexes(self):

        # -------------------------------------------------
        # PERMANENT IDENTIFIER
        #
        # VEN-xxxx can NEVER be reused.
        # -------------------------------------------------

        self.collection.create_index(
            [("vendor_code", ASCENDING)],
            unique=True,
        )

        # -------------------------------------------------
        # REUSABLE BUSINESS FIELDS
        #
        # Duplicate checking for these fields is handled
        # by VendorService using is_deleted=False.
        #
        # Therefore deleted Vendor data can be reused.
        # -------------------------------------------------

        self.collection.create_index(
            [("vendor_name", ASCENDING)]
        )

        self.collection.create_index(
            [("email", ASCENDING)]
        )

        self.collection.create_index(
            [("phone", ASCENDING)]
        )

        self.collection.create_index(
            [("gstin", ASCENDING)]
        )

        self.collection.create_index(
            [("pan", ASCENDING)]
        )

        self.collection.create_index(
            [("is_deleted", ASCENDING)]
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

    def find_duplicate(
            self,
            *,
            vendor_name: str | None = None,
            gstin: str | None = None,
            pan: str | None = None,
            email: str | None = None,
            phone: str | None = None,
            exclude_id: str | None = None,
    ):
        checks = {
            "vendor_name": vendor_name,
            "gstin": gstin,
            "pan": pan,
            "email": email,
            "phone": phone,
        }

        for field, value in checks.items():

            # Skip fields that are not being checked.
            if value is None or value == "":
                continue

            # Customer/vendor names and emails should
            # be checked case-insensitively.
            if field in {"vendor_name", "email"}:
                query = {
                    field: {
                        "$regex": f"^{re.escape(str(value))}$",
                        "$options": "i",
                    },
                    "is_deleted": False,
                }

            else:
                query = {
                    field: value,
                    "is_deleted": False,
                }

            if exclude_id:
                query["_id"] = {
                    "$ne": ObjectId(exclude_id)
                }

            if self.collection.find_one(query):
                return field

        return None

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