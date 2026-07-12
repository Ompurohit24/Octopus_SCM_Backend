from datetime import datetime

from backend.models.other_gov_agency_type import (
    OtherGovAgencyTypeCreate,
    OtherGovAgencyTypeUpdate,
)
from backend.repositories.other_gov_agency_type_repository import (
    other_gov_agency_type_repository,
)
from backend.utils.serializer import serialize, serialize_list


class OtherGovAgencyTypeService:

    @staticmethod
    def create(data: OtherGovAgencyTypeCreate, user_id: str):

        if other_gov_agency_type_repository.find_by_name(data.name):
            raise ValueError("Type already exists.")

        document = data.model_dump()

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

        result = other_gov_agency_type_repository.create(document)

        document["_id"] = result.inserted_id

        return serialize(document)

    @staticmethod
    def get_all(
        search="",
        skip=0,
        limit=50,
    ):

        data = other_gov_agency_type_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": other_gov_agency_type_repository.count(
                {
                    "is_deleted": False,
                }
            ),
            "items": serialize_list(data),
        }

    @staticmethod
    def update(
        item_id: str,
        data: OtherGovAgencyTypeUpdate,
    ):

        payload = data.model_dump(exclude_unset=True)

        payload["updated_at"] = datetime.utcnow()

        other_gov_agency_type_repository.update(
            item_id,
            payload,
        )

        return serialize(
            other_gov_agency_type_repository.find_by_id(item_id)
        )

    @staticmethod
    def delete(item_id: str):

        other_gov_agency_type_repository.soft_delete(item_id)

        return {
            "message": "Deleted successfully."
        }


other_gov_agency_type_service = OtherGovAgencyTypeService()