from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PurchaseOrderContainer(BaseModel):
    container_number: str
    size: str = ""


class PurchaseOrderCreate(BaseModel):
    job_id: str
    job_number: str

    consignee_name: str = ""

    # Snapshot job/workflow details into the PO.
    bl_no: str = ""
    be_no: str = ""
    cfs_name: str = ""

    # Only containers selected while creating this PO.
    containers: list[PurchaseOrderContainer] = Field(
        default_factory=list
    )

    category: Literal[
        "Other Gov Agency",
        "Other Services",
    ]

    service_name: str

    vendor_id: str
    vendor_code: Optional[str] = None
    vendor_name: str

    service_status: str

    unit: Optional[
        Literal["Container", "BL"]
    ] = None

    tariff: Optional[float] = None

    # Keep legacy fields for existing POs.
    tariff_20: Optional[float] = None
    tariff_40: Optional[float] = None

    enable_20: bool = False
    enable_40: bool = False


class PurchaseOrderUpdate(BaseModel):
    vendor_id: Optional[str] = None
    vendor_code: Optional[str] = None
    vendor_name: Optional[str] = None

    status: Optional[
        Literal[
            "Draft",
            "Issued",
            "Cancelled",
        ]
    ] = None


class PurchaseOrderResponse(BaseModel):
    id: str

    po_number: str

    job_id: str
    job_number: str

    consignee_name: str

    bl_no: str = ""
    be_no: str = ""
    cfs_name: str = ""

    containers: list[PurchaseOrderContainer] = Field(
        default_factory=list
    )

    category: str
    service_name: str

    vendor_id: str
    vendor_code: Optional[str] = None
    vendor_name: str

    service_status: str

    unit: Optional[str] = None

    tariff: Optional[float] = None

    # Legacy compatibility.
    tariff_20: Optional[float] = None
    tariff_40: Optional[float] = None

    enable_20: bool = False
    enable_40: bool = False

    status: str = "Issued"

    created_at: datetime
    updated_at: datetime