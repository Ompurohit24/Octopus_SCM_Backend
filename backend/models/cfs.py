from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CFSBase(BaseModel):
    name: str


class CFSCreate(CFSBase):
    pass


class CFSUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class CFSInDB(CFSBase):
    is_active: bool = True
    is_deleted: bool = False

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CFSResponse(CFSInDB):
    id: str

    model_config = ConfigDict(from_attributes=True)