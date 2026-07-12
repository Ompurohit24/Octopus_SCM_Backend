from datetime import datetime

from backend.models.transporter import (
    TransporterCreate,
    TransporterUpdate,
)
from backend.repositories.transporter_repository import (
    transporter_repository,
)
from backend.utils.serializer import serialize, serialize_list


class TransporterService:

    @staticmethod
    def create(
        transporter: TransporterCreate,
        user_id: str,
    ):

        if transporter_repository.find_by_name(
            transporter.name
        ):
            raise ValueError(
                "Transporter already exists."
            )

        document = transporter.model_dump()

        document.update(
            {
                "is_active": True,
                "is_deleted": False,
                "created_by": user_id,
                "updated_by": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        result = transporter_repository.create(document)

        document["_id"] = result.inserted_id

        return serialize(document)

    @staticmethod
    def get_all(
        search="",
        skip=0,
        limit=50,
    ):

        transporters = transporter_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": transporter_repository.count(
                {
                    "is_deleted": False,
                }
            ),
            "items": serialize_list(
                transporters
            ),
        }

    @staticmethod
    def update(
        transporter_id: str,
        transporter: TransporterUpdate,
    ):

        data = transporter.model_dump(
            exclude_unset=True
        )

        data["updated_at"] = datetime.utcnow()

        transporter_repository.update(
            transporter_id,
            data,
        )

        return serialize(
            transporter_repository.find_by_id(
                transporter_id
            )
        )

    @staticmethod
    def delete(
        transporter_id: str,
    ):

        transporter_repository.soft_delete(
            transporter_id
        )

        return {
            "message": "Transporter deleted successfully."
        }


transporter_service = TransporterService()