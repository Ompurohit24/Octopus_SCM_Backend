from datetime import datetime, timezone

from backend.database.mongo import client
from backend.repositories.counter_repository import counter_repository
from backend.repositories.purchase_order_repository import (
    purchase_order_repository,
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

    def create(self, data: dict):

        existing = purchase_order_repository.get_by_service(
            job_id=data["job_id"],
            category=data["category"],
            service_name=data["service_name"],
        )

        if existing:
            raise ValueError(
                "Purchase Order already exists "
                "for this job and service."
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

        return self._serialize(created)

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