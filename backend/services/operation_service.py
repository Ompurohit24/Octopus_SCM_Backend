from fastapi import HTTPException, status

from backend.models.operation import (
    PubOperationCreate,
    PubOperationUpdate,
    ImportOperationCreate,
    ImportOperationUpdate,
)
from backend.repositories.operation_repository import (
    pub_operation_repository,
    import_operation_repository,
)
from backend.utils.serializer import serialize, serialize_list


class OperationService:

    def __init__(
        self,
        repository,
        entity_name: str,
    ):
        self.repository = repository
        self.entity_name = entity_name

    def list(
        self,
        search: str,
        skip: int,
        limit: int,
    ):
        operations = self.repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": self.repository.count(
                {
                    "is_deleted": False,
                }
            ),
            "skip": skip,
            "limit": limit,
            "items": serialize_list(operations),
        }

    def get(self, operation_id: str):
        operation = self.repository.get(operation_id)

        if not operation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name} not found.",
            )

        return serialize(operation)

    def create(self, operation):
        duplicate = self.repository.find_duplicate(
            email=str(operation.email),
            mobile_number=operation.mobile_number,
        )

        if duplicate:
            messages = {
                "email": "Email already exists.",
                "mobile_number": "Mobile Number already exists.",
            }

            raise ValueError(messages[duplicate])

        document = operation.model_dump()

        created_operation = self.repository.create(
            document
        )

        return serialize(created_operation)

    def update(
        self,
        operation_id: str,
        operation,
    ):
        existing = self.repository.get(operation_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name} not found.",
            )

        merged = {
            **existing,
            **operation.model_dump(exclude_unset=True),
        }

        duplicate = self.repository.find_duplicate(
            email=str(merged["email"]),
            mobile_number=merged["mobile_number"],
            exclude_id=operation_id,
        )

        if duplicate:
            messages = {
                "email": "Email already exists.",
                "mobile_number": "Mobile Number already exists.",
            }

            raise ValueError(messages[duplicate])

        self.repository.update(
            operation_id,
            operation.model_dump(exclude_unset=True),
        )

        updated_operation = self.repository.get(
            operation_id
        )

        return serialize(updated_operation)

    def delete(self, operation_id: str):
        if not self.repository.get(operation_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name} not found.",
            )

        self.repository.delete(operation_id)

        return {
            "message": (
                f"{self.entity_name} deleted successfully."
            )
        }


pub_operation_service = OperationService(
    repository=pub_operation_repository,
    entity_name="Pub Operation",
)

import_operation_service = OperationService(
    repository=import_operation_repository,
    entity_name="Import Operation",
)