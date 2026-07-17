from backend.repositories.type_of_service_repository import (
    type_of_service_repository,
)


class TypeOfServiceService:
    def get_all(self, search=None):
        return type_of_service_repository.get_all(search)

    def create(self, name):
        return type_of_service_repository.create(name)

    def update(self, old_name, new_name):
        return type_of_service_repository.update(old_name, new_name)

    def delete(self, name):
        return type_of_service_repository.delete(name)


type_of_service_service = TypeOfServiceService()