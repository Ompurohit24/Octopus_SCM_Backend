from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


StatusType = Literal["Pending", "Done"]
YesNoType = Literal["Yes", "No"]


class ImportWorkflowBase(BaseModel):
    job_id: str
    job_number: str

    checklist: StatusType = "Pending"

    igm_no: Optional[str] = None
    igm_date: Optional[datetime] = None
    igm_status: StatusType = "Pending"

    inward_date: Optional[datetime] = None

    be_no: Optional[str] = None
    be_date: Optional[datetime] = None

    goods_registration: StatusType = "Pending"

    other_gov_agency: YesNoType = "No"
    other_gov_agency_type: Optional[str] = None

    assessment_type: Optional[str] = None
    cfs_name: Optional[str] = None

    boe_copy_mailed: StatusType = "Pending"

    original_documents: StatusType = "Pending"

    co_deface_required: YesNoType = "No"
    co_deface: Optional[StatusType] = None

    duty_payment: StatusType = "Pending"

    out_of_charge: StatusType = "Pending"

    oc_mail_sent: StatusType = "Pending"

    liner_invoice_received: StatusType = "Pending"

    liner_payment: StatusType = "Pending"

    payment_confirmation: StatusType = "Pending"

    do_received: StatusType = "Pending"
    do_validity: Optional[datetime] = None
    do_type: Optional[str] = None

    transportation: Optional[str] = None
    transporter: Optional[str] = None

    empty_container_return: StatusType = "Pending"

    container_unloaded: StatusType = "Pending"

    detention: StatusType = "Pending"

    job_closed: StatusType = "Pending"

    remarks: Optional[str] = None


class ImportWorkflowCreate(ImportWorkflowBase):
    pass


class ImportWorkflowUpdate(BaseModel):
    checklist: Optional[StatusType] = None

    igm_no: Optional[str] = None
    igm_date: Optional[datetime] = None
    igm_status: Optional[StatusType] = None

    inward_date: Optional[datetime] = None

    be_no: Optional[str] = None
    be_date: Optional[datetime] = None

    goods_registration: Optional[StatusType] = None

    other_gov_agency: Optional[YesNoType] = None
    other_gov_agency_type: Optional[str] = None

    assessment_type: Optional[str] = None
    cfs_name: Optional[str] = None

    boe_copy_mailed: Optional[StatusType] = None

    original_documents: Optional[StatusType] = None

    co_deface_required: Optional[YesNoType] = None
    co_deface: Optional[StatusType] = None

    duty_payment: Optional[StatusType] = None

    out_of_charge: Optional[StatusType] = None

    oc_mail_sent: Optional[StatusType] = None

    liner_invoice_received: Optional[StatusType] = None

    liner_payment: Optional[StatusType] = None

    payment_confirmation: Optional[StatusType] = None

    do_received: Optional[StatusType] = None
    do_validity: Optional[datetime] = None
    do_type: Optional[str] = None

    transportation: Optional[str] = None
    transporter: Optional[str] = None

    empty_container_return: Optional[StatusType] = None

    container_unloaded: Optional[StatusType] = None

    detention: Optional[StatusType] = None

    job_closed: Optional[StatusType] = None

    remarks: Optional[str] = None


class ImportWorkflowInDB(ImportWorkflowBase):
    is_active: bool = True
    is_deleted: bool = False

    current_stage: str = "checklist"

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ImportWorkflowResponse(ImportWorkflowInDB):
    id: str

    model_config = ConfigDict(from_attributes=True)