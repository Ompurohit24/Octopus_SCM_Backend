from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.models.user import UserCreate, UserLogin
from backend.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register(user: UserCreate):
    try:
        return AuthService.register(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login")
def login(data: UserLogin):
    try:
        return AuthService.login(data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh")
def refresh_token(
    data: RefreshTokenRequest,
):
    try:
        return AuthService.refresh(
            data.refresh_token
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )