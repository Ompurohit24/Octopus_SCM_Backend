from datetime import datetime, timezone

from backend.repositories.purchase_order_repository import (
    purchase_order_repository,
)
from backend.repositories.vendor_repository import (
    vendor_repository,
)
from backend.services.email_service import (
    email_service,
)


class InvoiceReminderService:

    def send_daily_invoice_reminders(self):
        """
        Send invoice reminders for Purchase Orders where:

            status == Issued

        AND

            invoice_status == Pending
            OR invoice_status is missing/None

        A successful email updates:

            last_invoice_reminder_at
            invoice_reminder_count

        Received invoices and Cancelled POs are excluded
        by the repository query.
        """

        purchase_orders = (
            purchase_order_repository
            .get_pending_invoice_reminders()
        )

        summary = {
            "eligible": len(
                purchase_orders
            ),
            "sent": 0,
            "skipped": 0,
            "failed": 0,
        }

        for purchase_order in purchase_orders:

            po_number = (
                purchase_order.get(
                    "po_number",
                    "",
                )
            )

            try:

                # -----------------------------------------
                # RE-CHECK CURRENT PO STATE
                #
                # The invoice may have been uploaded or
                # the PO cancelled after the initial query.
                # -----------------------------------------

                current_po = (
                    purchase_order_repository
                    .get_by_id(
                        purchase_order["_id"]
                    )
                )

                if not current_po:

                    summary[
                        "skipped"
                    ] += 1

                    continue

                if (
                    current_po.get(
                        "status"
                    )
                    != "Issued"
                ):

                    summary[
                        "skipped"
                    ] += 1

                    continue

                invoice_status = (
                    current_po.get(
                        "invoice_status"
                    )
                )

                if invoice_status not in (
                    None,
                    "Pending",
                ):

                    summary[
                        "skipped"
                    ] += 1

                    continue

                # -----------------------------------------
                # GET ASSIGNED VENDOR
                # -----------------------------------------

                vendor_id = (
                    current_po.get(
                        "vendor_id"
                    )
                )

                if not vendor_id:

                    print(
                        "[Invoice Reminder] "
                        f"{po_number}: "
                        "vendor_id missing.",
                        flush=True,
                    )

                    summary[
                        "skipped"
                    ] += 1

                    continue

                vendor = (
                    vendor_repository
                    .find_by_id(
                        vendor_id
                    )
                )

                if not vendor:

                    print(
                        "[Invoice Reminder] "
                        f"{po_number}: "
                        "vendor not found.",
                        flush=True,
                    )

                    summary[
                        "skipped"
                    ] += 1

                    continue

                # -----------------------------------------
                # SEND EMAIL
                # -----------------------------------------

                sent = (
                    email_service
                    .send_purchase_order_invoice_reminder_email(
                        vendor=vendor,
                        purchase_order=current_po,
                    )
                )

                if not sent:

                    print(
                        "[Invoice Reminder] "
                        f"{po_number}: "
                        "vendor email missing.",
                        flush=True,
                    )

                    summary[
                        "skipped"
                    ] += 1

                    continue

                # -----------------------------------------
                # RECORD SUCCESSFUL REMINDER
                #
                # Repository performs another atomic
                # Issued + Pending check.
                # -----------------------------------------

                recorded = (
                    purchase_order_repository
                    .mark_invoice_reminder_sent(
                        po_id=current_po[
                            "_id"
                        ],
                        sent_at=datetime.now(
                            timezone.utc
                        ),
                    )
                )

                if recorded:

                    summary[
                        "sent"
                    ] += 1

                    print(
                        "[Invoice Reminder] "
                        f"{po_number}: sent.",
                        flush=True,
                    )

                else:

                    # Email was sent, but PO state changed
                    # before reminder audit was recorded.
                    #
                    # Do not count this as another failure
                    # requiring a retry in this same run.

                    summary[
                        "skipped"
                    ] += 1

                    print(
                        "[Invoice Reminder] "
                        f"{po_number}: email sent, "
                        "but PO state changed before "
                        "audit update.",
                        flush=True,
                    )

            except Exception as exc:

                summary[
                    "failed"
                ] += 1

                print(
                    "[Invoice Reminder Error] "
                    f"{po_number}: "
                    f"{repr(exc)}",
                    flush=True,
                )

        return summary


invoice_reminder_service = (
    InvoiceReminderService()
)