from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import BaseRepository

transporters = db["transporters"]


class TransporterRepository(BaseRepository):

    def __init__(self):
        super().__init__(transporters)

    def create_indexes(self):

        self.collection.create_index(
            [("name", ASCENDING)],
            unique=True,
        )

    def find_by_name(self, name: str):

        return self.collection.find_one(
            {
                "name": name,
                "is_deleted": False,
            }
        )

    def search(
        self,
        search: str = "",
        skip: int = 0,
        limit: int = 50,
    ):

        query = {
            "is_deleted": False,
        }

        if search:

            query["name"] = {
                "$regex": search,
                "$options": "i",
            }

        return self.list(
            query=query,
            skip=skip,
            limit=limit,
            sort_field="name",
        )


transporter_repository = TransporterRepository()