from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository

companies = db["companies"]


class CompanyRepository(BaseRepository):

    def __init__(self):
        super().__init__(companies)

    def create_indexes(self):
        self.collection.create_index(
            [("company_code", 1)],
            name="company_code_unique",
            unique=True,
        )

        self.collection.create_index(
            [("company_name", 1)],
            name="company_name_unique",
            unique=True,
        )

        self.collection.create_index(
            [("email", 1)],
            name="company_email",
        )

    def find_by_name(self, name):

        return self.collection.find_one(
            {
                "company_name": name,
                "is_deleted": False,
            }
        )


company_repository = CompanyRepository()