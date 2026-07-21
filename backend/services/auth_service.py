from datetime import datetime

from backend.config.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_password,
    verify_password,
)
from backend.models.user import UserCreate, UserLogin
from backend.repositories.auth_repository import AuthRepository


class AuthService:

    @staticmethod
    def register(user: UserCreate):

        existing = AuthRepository.get_by_email(user.email)

        if existing:
            raise ValueError("Email already exists")

        document = {
            "full_name": user.full_name,
            "email": user.email,
            "hashed_password": hash_password(user.password),
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = AuthRepository.create(document)

        return {
            "id": str(result.inserted_id),
            "full_name": document["full_name"],
            "email": document["email"],
            "role": document["role"],
            "is_active": document["is_active"],
            "created_at": document["created_at"],
            "updated_at": document["updated_at"],
        }

    @staticmethod
    def login(data: UserLogin):

        user = AuthRepository.get_by_email(
            data.email
        )

        if not user:
            raise ValueError(
                "Invalid credentials"
            )

        if not verify_password(
                data.password,
                user["hashed_password"],
        ):
            raise ValueError(
                "Invalid credentials"
            )

        token_data = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
        }

        access_token = create_access_token(
            token_data
        )

        refresh_token = create_refresh_token(
            token_data
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh(
            refresh_token: str,
    ):

        payload = verify_refresh_token(
            refresh_token
        )

        if not payload:
            raise ValueError(
                "Invalid or expired refresh token"
            )

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        if not user_id:
            raise ValueError(
                "Invalid refresh token"
            )

        new_access_token = (
            create_access_token(
                {
                    "sub": user_id,
                    "email": email,
                    "role": role,
                }
            )
        )

        return {
            "access_token":
                new_access_token,
            "token_type":
                "bearer",
        }