from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ImportJobBase(BaseModel):
    bl_no: str
    bl_date: datetime

    invoice_no: str
    invoice_date: datetime

    no_of_cntr: int
    size: int

    # Multiple container numbers for this import job
    container_numbers: list[str] = Field(default_factory=list)

    line_name: str
    forwarder: str

    eta: datetime

    consignee_name: str
    consignee_address: str

    cargo_description: str


class ImportJobCreate(ImportJobBase):
    pass


class ImportJobUpdate(ImportJobBase):
    pass


class ImportJobInDB(ImportJobBase):
    job_number: str

    is_active: bool = True
    is_deleted: bool = False

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ImportJobResponse(ImportJobInDB):
    id: str

    model_config = ConfigDict(from_attributes=True)