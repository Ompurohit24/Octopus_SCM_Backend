from apscheduler.schedulers.background import (
    BackgroundScheduler,
)
from apscheduler.triggers.cron import (
    CronTrigger,
)

from backend.services.pending_job_email_service import (
    pending_job_email_service,
)
from backend.services.invoice_reminder_service import (
    invoice_reminder_service,
)


scheduler = BackgroundScheduler(
    timezone="Asia/Kolkata",
)


# =========================================================
# PENDING JOBS REPORT
# =========================================================

def send_pending_jobs_report():
    try:

        result = (
            pending_job_email_service
            .send_daily_pending_report()
        )

        print(
            "[Pending Jobs Scheduler]",
            result,
            flush=True,
        )

    except Exception as exc:

        print(
            "[Pending Jobs Scheduler Error]",
            repr(exc),
            flush=True,
        )


# =========================================================
# VENDOR INVOICE REMINDERS
# =========================================================

def send_vendor_invoice_reminders():
    """
    Runs daily at 10:00 AM IST.

    Sends reminders only for:

        PO status = Issued

    AND

        invoice_status = Pending/missing

    Once invoice_status becomes Received,
    or PO becomes Cancelled, reminders stop
    automatically.
    """

    try:

        result = (
            invoice_reminder_service
            .send_daily_invoice_reminders()
        )

        print(
            "[Invoice Reminder Scheduler]",
            result,
            flush=True,
        )

    except Exception as exc:

        print(
            "[Invoice Reminder Scheduler Error]",
            repr(exc),
            flush=True,
        )


# =========================================================
# START
# =========================================================

def start_scheduler():

    if scheduler.running:
        return

    # -----------------------------------------------------
    # EXISTING PENDING JOBS REPORT
    #
    # Keep existing schedule unchanged:
    # 11:05 PM IST
    # -----------------------------------------------------

    scheduler.add_job(
        send_pending_jobs_report,

        trigger=CronTrigger(
            hour=23,
            minute=5,
            timezone="Asia/Kolkata",
        ),

        id="daily_pending_jobs_email",

        name=(
            "Daily Pending Jobs Email"
        ),

        replace_existing=True,

        max_instances=1,

        coalesce=True,
    )

    # -----------------------------------------------------
    # VENDOR INVOICE REMINDER
    #
    # Every day:
    # 10:00 AM IST
    # -----------------------------------------------------

    scheduler.add_job(
        send_vendor_invoice_reminders,
        trigger=CronTrigger(
            hour=10,
            minute=00,
            timezone="Asia/Kolkata",
        ),
        id="daily_vendor_invoice_reminder",
        name="Daily Vendor Invoice Reminder",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    print(
        "[Scheduler] Daily Pending Jobs email "
        "scheduled for 11:05 PM IST.",
        flush=True,
    )

    print(
        "[Scheduler] Vendor Invoice Reminder "
        "scheduled for 10:00 AM IST.",
        flush=True,
    )


# =========================================================
# STOP
# =========================================================

def stop_scheduler():

    if scheduler.running:

        scheduler.shutdown(
            wait=False,
        )