from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class VendorCreate(BaseModel):
    vendor_code: str
    vendor_name: str

    address: str

    email: EmailStr
    countryCode: str
    phone: str

    gstin: str
    pan: str

    type_of_service: str


class VendorUpdate(BaseModel):
    vendor_code: Optional[str] = None
    vendor_name: Optional[str] = None

    address: Optional[str] = None

    email: Optional[EmailStr] = None
    countryCode: Optional[str] = None
    phone: Optional[str] = None

    gstin: Optional[str] = None
    pan: Optional[str] = None

    type_of_service: Optional[str] = None


class VendorResponse(BaseModel):
    id: str = Field(alias="_id")

    vendor_code: str
    vendor_name: str

    address: str

    email: EmailStr
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