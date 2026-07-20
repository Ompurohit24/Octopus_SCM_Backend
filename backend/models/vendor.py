from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


class VendorCreate(BaseModel):
    vendor_code: str
    vendor_name: str

    address: str

    # Supports:
    # email: "vendor@example.com"
    #
    # and:
    # email: [
    #     "vendor@example.com",
    #     "accounts@example.com",
    # ]
    #
    # Internally always normalized to a list.
    email: list[EmailStr]

    countryCode: str
    phone: str

    gstin: str
    pan: str

    type_of_service: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_emails(cls, value):
        if value is None:
            return []

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return []

            return [value]

        if isinstance(value, list):
            cleaned = []
            seen = set()

            for item in value:
                if item is None:
                    continue

                email = str(item).strip()

                if not email:
                    continue

                normalized = email.lower()

                if normalized in seen:
                    continue

                seen.add(normalized)
                cleaned.append(email)

            return cleaned

        return value


class VendorUpdate(BaseModel):
    vendor_code: Optional[str] = None
    vendor_name: Optional[str] = None

    address: Optional[str] = None

    # Supports existing string values as well as new arrays.
    email: Optional[list[EmailStr]] = None

    countryCode: Optional[str] = None
    phone: Optional[str] = None

    gstin: Optional[str] = None
    pan: Optional[str] = None

    type_of_service: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_emails(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return []

            return [value]

        if isinstance(value, list):
            cleaned = []
            seen = set()

            for item in value:
                if item is None:
                    continue

                email = str(item).strip()

                if not email:
                    continue

                normalized = email.lower()

                if normalized in seen:
                    continue

                seen.add(normalized)
                cleaned.append(email)

            return cleaned

        return value


class VendorResponse(BaseModel):
    id: str = Field(alias="_id")

    vendor_code: str
    vendor_name: str

    address: str

    email: list[EmailStr]

    country_code: str
    phone: str

    gstin: str
    pan: str

    type_of_service: str

    is_active: bool = True
    is_deleted: bool = False

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }