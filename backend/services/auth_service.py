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

        if not user_id:
            raise ValueError(
                "Invalid refresh token"
            )

        # Verify that the user still exists.
        try:
            user = AuthRepository.get_by_id(
                user_id
            )
        except Exception:
            raise ValueError(
                "Invalid refresh token"
            )

        if not user:
            raise ValueError(
                "User not found"
            )

        if not user.get(
                "is_active",
                True,
        ):
            raise ValueError(
                "User account is inactive"
            )

        # Use current user information from DB.
        token_data = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
        }

        new_access_token = (
            create_access_token(
                token_data
            )
        )

        return {
            "access_token":
                new_access_token,

            # Return the existing valid refresh
            # token so frontend session state
            # remains complete.
            "refresh_token":
                refresh_token,

            "token_type":
                "bearer",
        }