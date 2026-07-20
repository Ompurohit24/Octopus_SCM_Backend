from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=150)
    address: str

    # Supports one or multiple email addresses.
    # Internally, emails are always normalized to a list.
    email: list[EmailStr]

    countryCode: str = "+91"
    phone: str

    gstin: str
    gst_document: Optional[str] = None

    pan: str
    pan_document: Optional[str] = None

    tan: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_emails(cls, value):
        if value is None:
            return []

        # Backward compatibility:
        # "abc@example.com" -> ["abc@example.com"]
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

                if normalized not in seen:
                    seen.add(normalized)
                    cleaned.append(email)

            return cleaned

        return value


class CustomerCreate(CustomerBase):
    customer_code: str | None = None


class CustomerUpdate(CustomerBase):
    pass


class CustomerInDB(CustomerBase):
    customer_code: str

    is_active: bool = True
    is_deleted: bool = False

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CustomerResponse(CustomerInDB):
    id: str

    model_config = ConfigDict(from_attributes=True)