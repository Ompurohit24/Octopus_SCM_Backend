from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Address(BaseModel):
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None


class CompanyBase(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=150)

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    gstin: Optional[str] = None
    pan: Optional[str] = None

    currency: str = "INR"

    address: Address = Address()


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: str
    company_code: str

    is_active: bool
    is_deleted: bool

    created_by: str
    updated_by: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)