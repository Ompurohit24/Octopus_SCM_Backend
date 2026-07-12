from bson import ObjectId

from backend.database.mongo import db

users_collection = db["users"]


class AuthRepository:

    @staticmethod
    def get_by_email(email: str):
        return users_collection.find_one({"email": email})

    @staticmethod
    def create(document: dict):
        return users_collection.insert_one(document)

    @staticmethod
    def get_by_id(user_id: str):
        return users_collection.find_one(
            {"_id": ObjectId(user_id)}
        )

    @staticmethod
    def update(user_id: str, data: dict):
        return users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data},
        )

    @staticmethod
    def delete(user_id: str):
        return users_collection.delete_one(
            {"_id": ObjectId(user_id)}
        )

    @staticmethod
    def list():
        return list(
            users_collection.find(
                {},
                {"hashed_password": 0},
            )
        )