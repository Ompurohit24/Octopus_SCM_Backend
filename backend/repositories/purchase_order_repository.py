from datetime import datetime, timezone

from backend.database.mongo import db


purchase_orders = db["purchase_orders"]


class PurchaseOrderRepository:

    @staticmethod
    def create(
        data: dict,
        session=None,
    ):
        result = purchase_orders.insert_one(
            data,
            session=session,
        )

        return purchase_orders.find_one(
            {
                "_id": result.inserted_id
            },
            session=session,
        )

    @staticmethod
    def get_by_id(
        po_id,
    ):
        return purchase_orders.find_one(
            {
                "_id": po_id
            }
        )

    @staticmethod
    def get_by_po_number(
        po_number: str,
    ):
        return purchase_orders.find_one(
            {
                "po_number": po_number
            }
        )

    @staticmethod
    def get_by_service(
        job_id: str,
        category: str,
        service_name: str,
    ):
        """
        Returns an active PO for the selected
        workflow service.

        Cancelled POs do not block creation
        of a new PO.
        """

        return purchase_orders.find_one(
            {
                "job_id": job_id,
                "category": category,
                "service_name": service_name,

                "status": {
                    "$ne": "Cancelled"
                },
            }
        )

    @staticmethod
    def get_issued_by_service(
        job_id: str,
        category: str,
        service_name: str,
    ):
        """
        Used before removing/unchecking
        a workflow service.

        Only an Issued PO requires
        cancellation confirmation.
        """

        return purchase_orders.find_one(
            {
                "job_id": job_id,
                "category": category,
                "service_name": service_name,
                "status": "Issued",
            }
        )

    @staticmethod
    def list_all(
        search: str = "",
        skip: int = 0,
        limit: int = 100,
    ):
        query = {}

        if search:
            query = {
                "$or": [
                    {
                        "po_number": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "job_number": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "consignee_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "vendor_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "service_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                ]
            }

        total = (
            purchase_orders.count_documents(
                query
            )
        )

        items = list(
            purchase_orders
            .find(query)
            .sort(
                "created_at",
                -1,
            )
            .skip(skip)
            .limit(limit)
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items,
        }

    @staticmethod
    def update(
        po_id,
        data: dict,
    ):
        purchase_orders.update_one(
            {
                "_id": po_id
            },
            {
                "$set": data
            },
        )

        return purchase_orders.find_one(
            {
                "_id": po_id
            }
        )

    @staticmethod
    def cancel_issued_po(
        po_id,
        reason: str,
        session=None,
    ):
        """
        Atomically cancel an Issued Purchase Order.

        The status condition prevents an already
        cancelled PO from being cancelled again
        by concurrent requests.

        Cancelled POs are automatically excluded
        from invoice reminders because reminder
        queries require status == Issued.
        """

        now = datetime.now(
            timezone.utc
        )

        result = purchase_orders.update_one(
            {
                "_id": po_id,
                "status": "Issued",
            },
            {
                "$set": {
                    "status": "Cancelled",

                    "cancellation_reason":
                        reason,

                    "cancelled_at":
                        now,

                    "updated_at":
                        now,
                }
            },
            session=session,
        )

        if result.modified_count == 0:
            return None

        return purchase_orders.find_one(
            {
                "_id": po_id
            },
            session=session,
        )

    # =============================================
    # VENDOR INVOICE
    # =============================================

    @staticmethod
    def mark_invoice_received(
        po_id,
        file_path: str,
        original_name: str,
        content_type: str | None,
        session=None,
    ):
        """
        Mark the vendor invoice as received.

        Invoice upload is allowed only while
        the Purchase Order is Issued.

        This same operation also supports replacing
        an existing invoice. invoice_status remains
        Received, therefore reminders do not restart.
        """

        now = datetime.now(
            timezone.utc
        )

        result = purchase_orders.update_one(
            {
                "_id": po_id,
                "status": "Issued",
            },
            {
                "$set": {
                    "invoice_status":
                        "Received",

                    "invoice_file_path":
                        file_path,

                    "invoice_original_name":
                        original_name,

                    "invoice_content_type":
                        content_type,

                    "invoice_received_at":
                        now,

                    "updated_at":
                        now,
                }
            },
            session=session,
        )

        if result.matched_count == 0:
            return None

        return purchase_orders.find_one(
            {
                "_id": po_id
            },
            session=session,
        )

    @staticmethod
    def get_pending_invoice_reminders():
        """
        Return every Purchase Order eligible for the
        daily vendor invoice reminder.

        Required conditions:

            PO status == Issued

        AND

            invoice_status == Pending

        Existing/legacy POs may not yet contain
        invoice_status. Missing invoice_status is
        therefore treated as Pending.

        Received and Cancelled POs are excluded.
        """

        return list(
            purchase_orders.find(
                {
                    "status": "Issued",

                    "$or": [
                        {
                            "invoice_status":
                                "Pending"
                        },
                        {
                            "invoice_status": {
                                "$exists": False
                            }
                        },
                        {
                            "invoice_status":
                                None
                        },
                    ],
                }
            ).sort(
                "created_at",
                1,
            )
        )

    @staticmethod
    def mark_invoice_reminder_sent(
        po_id,
        sent_at=None,
    ):
        """
        Record a successfully sent invoice reminder.

        Increment only after email delivery succeeds.

        This provides an audit trail:

            last_invoice_reminder_at
            invoice_reminder_count
        """

        if sent_at is None:
            sent_at = datetime.now(
                timezone.utc
            )

        result = purchase_orders.update_one(
            {
                "_id": po_id,

                # Protect against a race where the
                # invoice is uploaded or PO cancelled
                # while reminders are being processed.
                "status": "Issued",

                "$or": [
                    {
                        "invoice_status":
                            "Pending"
                    },
                    {
                        "invoice_status": {
                            "$exists": False
                        }
                    },
                    {
                        "invoice_status":
                            None
                    },
                ],
            },
            {
                "$set": {
                    "last_invoice_reminder_at":
                        sent_at,

                    "updated_at":
                        sent_at,
                },

                "$inc": {
                    "invoice_reminder_count":
                        1
                },
            },
        )

        return (
            result.modified_count > 0
        )


purchase_order_repository = (
    PurchaseOrderRepository()
)