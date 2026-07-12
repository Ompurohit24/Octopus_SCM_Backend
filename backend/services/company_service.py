from datetime import datetime

from backend.repositories.company_repository import company_repository
from backend.repositories.counter_repository import counter_repository
from backend.utils.serializer import serialize, serialize_list


class CompanyService:

    @staticmethod
    def generate_code():

        number = counter_repository.next("company")

        return f"COM-{number:06d}"

    @staticmethod
    def create(company, user_id):

        if company_repository.find_by_name(company.company_name):
            raise ValueError("Company already exists")

        document = company.model_dump()

        document.update({
            "company_code": CompanyService.generate_code(),
            "is_active": True,
            "is_deleted": False,
            "created_by": user_id,
            "updated_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        result = company_repository.create(document)

        document["_id"] = result.inserted_id

        return serialize(document)

    @staticmethod
    def get_all():

        return serialize_list(
            company_repository.list()
        )