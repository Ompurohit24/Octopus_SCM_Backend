from datetime import datetime
from backend.repositories.line_name_repository import (
    line_name_repository,
)
from backend.repositories.import_job_repository import (
    import_job_repository,
)
from backend.utils.serializer import serialize, serialize_list


class LineNameService:

    @staticmethod
    def get_all(search: str = ""):
        return serialize_list(
            line_name_repository.search(
                search=search,
                limit=500,
            )
        )

    @staticmethod
    def create(name: str):

        name = name.strip()

        if not name:
            raise ValueError("Line Name is required.")

        document = {
            "name": name,
            "is_active": True,
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = line_name_repository.create(document)
        document["_id"] = result.inserted_id

        return serialize(document)

    @staticmethod
    def delete(name: str):

        if import_job_repository.is_line_name_in_use(name):
            raise ValueError(
                "Cannot delete. This Line Name is already used in Import Jobs."
            )

        line = line_name_repository.find_by_name(name)

        if not line:
            raise ValueError("Line Name not found.")

        line_name_repository.soft_delete(str(line["_id"]))

        return {
            "message": "Line Name deleted successfully."
        }

    @staticmethod
    def update(
            old_name: str,
            new_name: str,
    ):
        new_name = new_name.strip()

        if not new_name:
            raise ValueError("Line Name is required.")

        line_name_repository.update(
            old_name,
            new_name,
        )

        return {
            "message": "Line Name updated successfully."
        }


line_name_service = LineNameService()