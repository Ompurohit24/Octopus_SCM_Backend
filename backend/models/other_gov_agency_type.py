from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OtherGovAgencyTypeBase(BaseModel):
    name: str


class OtherGovAgencyTypeCreate(OtherGovAgencyTypeBase):
    pass


class OtherGovAgencyTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class OtherGovAgencyTypeInDB(OtherGovAgencyTypeBase):
    is_active: bool = True
    is_deleted: bool = False

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OtherGovAgencyTypeResponse(OtherGovAgencyTypeInDB):
    id: str

    model_config = ConfigDict(from_attributes=True)