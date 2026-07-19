from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.services.pending_job_email_service import (
    pending_job_email_service,
)


scheduler = BackgroundScheduler(
    timezone="Asia/Kolkata",
)


def send_pending_jobs_report():
    try:
        result = (
            pending_job_email_service
            .send_daily_pending_report()
        )

        print(
            "[Pending Jobs Scheduler]",
            result,
        )

    except Exception as exc:
        print(
            "[Pending Jobs Scheduler Error]",
            repr(exc),
        )


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        send_pending_jobs_report,
        trigger=CronTrigger(
            hour=23,
            minute=0,
            timezone="Asia/Kolkata",
        ),
        id="daily_pending_jobs_email",
        name="Daily Pending Jobs Email",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    print(
        "[Scheduler] Pending Jobs email scheduled "
        "daily at 11:00 PM IST."
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(
            wait=False,
        )