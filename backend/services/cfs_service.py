from datetime import datetime

from backend.models.cfs import CFSCreate, CFSUpdate
from backend.repositories.cfs_repository import cfs_repository
from backend.utils.serializer import serialize, serialize_list


class CFSService:

    @staticmethod
    def create(cfs: CFSCreate, user_id: str):

        existing = cfs_repository.find_by_name(cfs.name)

        if existing:
            raise ValueError("CFS already exists.")

        document = cfs.model_dump()

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

        result = cfs_repository.create(document)

        document["_id"] = result.inserted_id

        return serialize(document)

    @staticmethod
    def get_all(
        search="",
        skip=0,
        limit=50,
    ):

        data = cfs_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": cfs_repository.count(
                {
                    "is_deleted": False,
                }
            ),
            "items": serialize_list(data),
        }

    @staticmethod
    def update(
        cfs_id: str,
        cfs: CFSUpdate,
    ):

        data = cfs.model_dump(exclude_unset=True)

        data["updated_at"] = datetime.utcnow()

        cfs_repository.update(
            cfs_id,
            data,
        )

        return serialize(
            cfs_repository.find_by_id(cfs_id)
        )

    @staticmethod
    def delete(cfs_id: str):

        cfs_repository.soft_delete(cfs_id)

        return {
            "message": "CFS deleted successfully."
        }


cfs_service = CFSService()