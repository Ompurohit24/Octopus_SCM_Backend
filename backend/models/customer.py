from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=150)
    address: str
    email: EmailStr
    phone: str
    gstin: str
    pan: str
    tan: str


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

