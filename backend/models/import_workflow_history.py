from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImportWorkflowHistoryBase(BaseModel):
    workflow_id: str
    job_id: str
    job_number: str

    field_name: str

    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


class ImportWorkflowHistoryCreate(ImportWorkflowHistoryBase):
    pass


class ImportWorkflowHistoryInDB(ImportWorkflowHistoryBase):
    changed_by: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImportWorkflowHistoryResponse(ImportWorkflowHistoryInDB):
    id: str

    model_config = ConfigDict(from_attributes=True)