from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pwdlib import PasswordHash

from backend.config.settings import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    data: dict,
) -> str:

    to_encode = data.copy()

    # Long-lived login session.
    #
    # User does not need to log in every
    # 160 minutes.
    #
    # 365 days is the session lifetime.
    expire = (
        datetime.now(timezone.utc)
        + timedelta(days=365)
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_access_token(
    token: str,
):

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
        )

        # Prevent refresh tokens from being
        # accepted as API access tokens.
        if (
            payload.get("token_type")
            != "access"
        ):
            return None

        return payload

    except JWTError:
        return None


def verify_refresh_token(
    token: str,
):

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
        )

        # Only refresh tokens can be used
        # to generate a new access token.
        if (
            payload.get("token_type")
            != "refresh"
        ):
            return None

        return payload

    except JWTError:
        return None