from datetime import datetime, timezone

from fastapi import BackgroundTasks

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


class PurchaseOrderService:

    SEQUENCE = "purchase_order"

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