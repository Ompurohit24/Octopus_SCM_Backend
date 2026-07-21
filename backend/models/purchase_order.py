from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


PurchaseOrderStatus = Literal[
    "Draft",
    "Issued",
    "Cancelled",
]

PurchaseOrderInvoiceStatus = Literal[
    "Pending",
    "Received",
]


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
        "Transportation",
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

    status: Optional[PurchaseOrderStatus] = None


class PurchaseOrderCancel(BaseModel):
    """
    Used when a service is removed/unselected from an
    Import Workflow after a Purchase Order has already
    been issued.

    Cancellation must preserve the PO for audit/history.
    """

    reason: Optional[str] = (
        "Service removed from Import Workflow"
    )


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

    status: PurchaseOrderStatus = "Issued"

    # ---------------------------------------------
    # INVOICE
    #
    # Pending:
    #   PO issued but vendor invoice not received.
    #
    # Received:
    #   Invoice uploaded into the system.
    #   Daily reminder emails must stop.
    # ---------------------------------------------

    invoice_status: PurchaseOrderInvoiceStatus = (
        "Pending"
    )

    invoice_file_path: Optional[str] = None
    invoice_original_name: Optional[str] = None
    invoice_content_type: Optional[str] = None

    invoice_received_at: Optional[datetime] = None

    # Reminder audit.
    last_invoice_reminder_at: Optional[datetime] = None
    invoice_reminder_count: int = 0

    # Cancellation audit information.
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime