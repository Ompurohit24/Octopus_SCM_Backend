from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TransporterBase(BaseModel):
    name: str


class TransporterCreate(TransporterBase):
    pass


class TransporterUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class TransporterInDB(TransporterBase):
    is_active: bool = True
    is_deleted: bool = False

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TransporterResponse(TransporterInDB):
    id: str

    model_config = ConfigDict(from_attributes=True)