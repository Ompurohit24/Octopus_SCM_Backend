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

        vendor = vendor_repository.get(
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
        #
        # Do this only AFTER MongoDB transaction commits.
        # ---------------------------------------------

        background_tasks.add_task(
            self._send_purchase_order_email,
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