from datetime import datetime, timezone
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import (
    BackgroundTasks,
    UploadFile,
)

from backend.database.mongo import client
from backend.repositories.counter_repository import (
    counter_repository,
)
from backend.repositories.purchase_order_repository import (
    purchase_order_repository,
)
from backend.repositories.vendor_repository import (
    vendor_repository,
)
from backend.services.email_service import (
    email_service,
)
from backend.services.purchase_order_pdf_service import (
    purchase_order_pdf_service,
)



INVOICE_ROOT = Path("Invoices")
INVOICE_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)


ALLOWED_INVOICE_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

ALLOWED_INVOICE_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

MAX_INVOICE_SIZE = (
    10 * 1024 * 1024
)



class PurchaseOrderService:

    SEQUENCE = "purchase_order"



    @staticmethod
    def _safe_path_component(
        value: str,
    ) -> str:
        """
        Keep job/PO folder names safe.

        Example:
            IMP-00023
            PO-00002
        """

        value = str(
            value or ""
        ).strip()

        safe = "".join(
            character
            for character in value
            if (
                character.isalnum()
                or character in {
                    "-",
                    "_",
                }
            )
        )

        if not safe:
            raise ValueError(
                "Invalid invoice storage path."
            )

        return safe

    @staticmethod
    def _serialize(item):
        if not item:
            return None

        item = dict(item)

        item["id"] = str(
            item.pop("_id")
        )

        return item

    @staticmethod
    def _send_purchase_order_email(
        vendor: dict,
        purchase_order: dict,
    ):
        """
        Background task.

        The PO has already been successfully committed
        to MongoDB before this method runs.

        PDF/email failure must not affect PO creation.
        """

        try:
            pdf_bytes = (
                purchase_order_pdf_service.generate(
                    purchase_order
                )
            )

            email_service.send_purchase_order_email(
                vendor=vendor,
                purchase_order=purchase_order,
                pdf_bytes=pdf_bytes,
            )

        except Exception as e:
            print(
                "Purchase Order email failed:",
                e,
            )

    @staticmethod
    def _send_purchase_order_cancellation_email(
        vendor: dict,
        purchase_order: dict,
    ):
        """
        Background task.

        Runs only after the PO cancellation has been
        successfully committed.

        Email failure must not roll back cancellation.
        """

        try:
            email_service.send_purchase_order_cancellation_email(
                vendor=vendor,
                purchase_order=purchase_order,
            )

        except Exception as e:
            print(
                "Purchase Order cancellation email failed:",
                e,
            )

    def create(
        self,
        data: dict,
        background_tasks: BackgroundTasks,
    ):

        existing = (
            purchase_order_repository.get_by_service(
                job_id=data["job_id"],
                category=data["category"],
                service_name=data["service_name"],
            )
        )

        if existing:
            raise ValueError(
                "Purchase Order already exists "
                "for this job and service."
            )

        # ---------------------------------------------
        # VALIDATE VENDOR BEFORE CREATING PO
        # ---------------------------------------------

        vendor = vendor_repository.find_by_id(
            data["vendor_id"]
        )

        if not vendor:
            raise ValueError(
                "Selected Vendor not found."
            )

        now = datetime.now(timezone.utc)

        with client.start_session() as session:

            with session.start_transaction():

                counter_repository.initialize(
                    self.SEQUENCE,
                    0,
                )

                sequence = counter_repository.next(
                    self.SEQUENCE,
                    session=session,
                )

                po_number = (
                    f"PO-{sequence:05d}"
                )

                document = {
                    **data,

                    "po_number": po_number,

                    "status": "Issued",

                    # Vendor invoice lifecycle starts as soon
                    # as the Purchase Order is issued.
                    "invoice_status": "Pending",

                    "invoice_file_path": None,
                    "invoice_original_name": None,
                    "invoice_content_type": None,
                    "invoice_received_at": None,

                    "last_invoice_reminder_at": None,
                    "invoice_reminder_count": 0,

                    "created_at": now,
                    "updated_at": now,
                }

                created = (
                    purchase_order_repository.create(
                        document,
                        session=session,
                    )
                )

        # ---------------------------------------------
        # TRANSACTION SUCCESSFULLY COMMITTED
        # ---------------------------------------------

        serialized_po = self._serialize(
            created
        )

        # ---------------------------------------------
        # SEND PDF + EMAIL IN BACKGROUND
        # ---------------------------------------------

        background_tasks.add_task(
            self._send_purchase_order_email,
            vendor,
            serialized_po,
        )

        return serialized_po

    def get_issued_for_service(
        self,
        job_id: str,
        category: str,
        service_name: str,
    ):
        """
        Check whether an Issued PO exists for the exact
        workflow service before the user unchecks it.

        Returns:
            {
                "has_issued_po": False
            }

        or:

            {
                "has_issued_po": True,
                "purchase_order": {...}
            }
        """

        purchase_order = (
            purchase_order_repository.get_issued_by_service(
                job_id=job_id,
                category=category,
                service_name=service_name,
            )
        )

        if not purchase_order:
            return {
                "has_issued_po": False,
                "purchase_order": None,
            }

        return {
            "has_issued_po": True,
            "purchase_order": self._serialize(
                purchase_order
            ),
        }

    def cancel_issued_service_po(
        self,
        job_id: str,
        category: str,
        service_name: str,
        reason: str,
        background_tasks: BackgroundTasks,
    ):
        """
        Cancel an Issued PO when its workflow service
        is removed/unselected.

        The PO is preserved for audit/history.

        This method does NOT modify the workflow itself.
        Workflow removal will happen only after this
        cancellation succeeds.
        """

        purchase_order = (
            purchase_order_repository.get_issued_by_service(
                job_id=job_id,
                category=category,
                service_name=service_name,
            )
        )

        if not purchase_order:
            raise ValueError(
                "No issued Purchase Order found "
                "for this job and service."
            )

        vendor = vendor_repository.find_by_id(
            purchase_order["vendor_id"]
        )

        if not vendor:
            raise ValueError(
                "Vendor assigned to this Purchase Order "
                "was not found."
            )

        with client.start_session() as session:

            with session.start_transaction():

                cancelled = (
                    purchase_order_repository.cancel_issued_po(
                        po_id=purchase_order["_id"],
                        reason=reason,
                        session=session,
                    )
                )

                if not cancelled:
                    raise ValueError(
                        "Purchase Order is no longer issued "
                        "or has already been cancelled."
                    )

        # ---------------------------------------------
        # TRANSACTION SUCCESSFULLY COMMITTED
        # ---------------------------------------------

        serialized_po = self._serialize(
            cancelled
        )

        # ---------------------------------------------
        # SEND CANCELLATION EMAIL AFTER COMMIT
        # ---------------------------------------------

        background_tasks.add_task(
            self._send_purchase_order_cancellation_email,
            vendor,
            serialized_po,
        )

        return serialized_po


    def upload_invoice(
        self,
        po_number: str,
        invoice: UploadFile,
    ):
        """
        Upload or replace a vendor invoice for an
        Issued Purchase Order.

        Lifecycle:

            Issued + Pending
                -> upload
                -> Received

            Issued + Received
                -> replace invoice
                -> Received

            Cancelled
                -> upload rejected

        Once invoice_status becomes Received,
        the PO is excluded from daily invoice
        reminder emails.
        """

        # ---------------------------------------------
        # GET PURCHASE ORDER
        # ---------------------------------------------

        purchase_order = (
            purchase_order_repository.get_by_po_number(
                po_number
            )
        )

        if not purchase_order:
            raise ValueError(
                "Purchase Order not found."
            )

        if (
            purchase_order.get(
                "status"
            )
            != "Issued"
        ):
            raise ValueError(
                "Invoice can only be uploaded "
                "for an Issued Purchase Order."
            )

        # ---------------------------------------------
        # VALIDATE FILE NAME
        # ---------------------------------------------

        original_name = (
            invoice.filename
            or ""
        ).strip()

        if not original_name:
            raise ValueError(
                "Invoice file is required."
            )

        # Never trust directory information supplied
        # as part of an uploaded filename.
        original_name = Path(
            original_name
        ).name

        extension = (
            Path(
                original_name
            )
            .suffix
            .lower()
        )

        if (
            extension
            not in
            ALLOWED_INVOICE_EXTENSIONS
        ):
            raise ValueError(
                "Invoice must be a PDF, JPG, "
                "JPEG, or PNG file."
            )

        content_type = (
            invoice.content_type
            or ""
        ).lower()

        if (
            content_type
            and content_type
            not in
            ALLOWED_INVOICE_CONTENT_TYPES
        ):
            raise ValueError(
                "Invalid invoice file type."
            )

        # ---------------------------------------------
        # PREPARE STORAGE
        # ---------------------------------------------

        job_number = (
            self._safe_path_component(
                purchase_order.get(
                    "job_number",
                    "",
                )
            )
        )

        safe_po_number = (
            self._safe_path_component(
                purchase_order.get(
                    "po_number",
                    "",
                )
            )
        )

        invoice_directory = (
            INVOICE_ROOT
            / job_number
            / safe_po_number
        )

        invoice_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Use a generated server filename.
        #
        # We still preserve the original filename
        # separately in MongoDB.
        stored_filename = (
            f"invoice_"
            f"{uuid4().hex}"
            f"{extension}"
        )

        final_path = (
            invoice_directory
            / stored_filename
        )

        temporary_path = (
            invoice_directory
            / (
                f".upload_"
                f"{uuid4().hex}"
                f".tmp"
            )
        )

        # ---------------------------------------------
        # SAVE FILE WITH SIZE LIMIT
        # ---------------------------------------------

        total_size = 0

        try:

            with temporary_path.open(
                "wb"
            ) as destination:

                while True:

                    chunk = (
                        invoice.file.read(
                            1024 * 1024
                        )
                    )

                    if not chunk:
                        break

                    total_size += len(
                        chunk
                    )

                    if (
                        total_size
                        >
                        MAX_INVOICE_SIZE
                    ):
                        raise ValueError(
                            "Invoice file size "
                            "must not exceed 10 MB."
                        )

                    destination.write(
                        chunk
                    )

            if total_size == 0:
                raise ValueError(
                    "Uploaded invoice file is empty."
                )

            # Atomic filesystem rename on the
            # same filesystem.
            temporary_path.replace(
                final_path
            )

        except Exception:

            if temporary_path.exists():
                temporary_path.unlink(
                    missing_ok=True
                )

            raise

        finally:

            try:
                invoice.file.close()
            except Exception:
                pass

        # ---------------------------------------------
        # DATABASE UPDATE
        # ---------------------------------------------

        old_invoice_path = (
            purchase_order.get(
                "invoice_file_path"
            )
        )

        try:

            updated = (
                purchase_order_repository
                .mark_invoice_received(
                    po_id=purchase_order["_id"],

                    file_path=str(
                        final_path
                    ),

                    original_name=
                        original_name,

                    content_type=(
                        content_type
                        or None
                    ),
                )
            )

            if not updated:

                # PO may have been cancelled between
                # validation and database update.

                final_path.unlink(
                    missing_ok=True
                )

                raise ValueError(
                    "Purchase Order is no longer "
                    "eligible for invoice upload."
                )

        except Exception:

            final_path.unlink(
                missing_ok=True
            )

            raise

        # ---------------------------------------------
        # REMOVE OLD FILE ONLY AFTER DB SUCCESS
        #
        # This supports Replace Invoice safely.
        # ---------------------------------------------

        if old_invoice_path:

            old_path = Path(
                old_invoice_path
            )

            try:

                if (
                    old_path.exists()
                    and
                    old_path.resolve()
                    != final_path.resolve()
                ):
                    old_path.unlink()

            except OSError as e:

                # Do not fail a successful invoice
                # upload just because stale-file
                # cleanup failed.

                print(
                    "Old invoice cleanup failed:",
                    e,
                )

        return self._serialize(
            updated
        )

    def list(
        self,
        search: str = "",
        skip: int = 0,
        limit: int = 100,
    ):
        result = (
            purchase_order_repository.list_all(
                search=search,
                skip=skip,
                limit=limit,
            )
        )

        result["items"] = [
            self._serialize(item)
            for item in result["items"]
        ]

        return result


purchase_order_service = PurchaseOrderService()