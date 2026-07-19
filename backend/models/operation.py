from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class PubOperationCreate(BaseModel):
    name: str
    mobile_number: str
    email: EmailStr


class PubOperationUpdate(BaseModel):
    name: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None


class PubOperationResponse(BaseModel):
    id: str = Field(alias="_id")

    name: str
    mobile_number: str
    email: EmailStr

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


class ImportOperationCreate(BaseModel):
    name: str
    mobile_number: str
    email: EmailStr


class ImportOperationUpdate(BaseModel):
    name: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[EmailStr] = None


class ImportOperationResponse(BaseModel):
    id: str = Field(alias="_id")

    name: str
    mobile_number: str
    email: EmailStr

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