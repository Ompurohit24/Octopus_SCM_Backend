from datetime import datetime
from typing import Any
from bson import ObjectId
from backend.database.mongo import db
from backend.services.email_service import email_service


class PendingJobEmailService:

    def __init__(self):
        self.import_jobs = db["import_jobs"]
        self.import_workflows = db["import_workflows"]

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _normalize(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip().lower()

    @staticmethod
    def _format_date(value: Any) -> str:
        if not value:
            return ""

        if isinstance(value, datetime):
            return value.strftime("%d-%m-%Y")

        return str(value)

    def _find_import_job(
            self,
            workflow: dict,
    ) -> dict | None:

        job_id = workflow.get("job_id")

        # ---------------------------------------------------------
        # PRIMARY MATCH: JOB ID
        # ---------------------------------------------------------

        if job_id:

            try:
                object_id = ObjectId(
                    str(job_id)
                )

                job = self.import_jobs.find_one(
                    {
                        "_id": object_id,
                        "is_deleted": {
                            "$ne": True,
                        },
                    }
                )

                if job:
                    return job

            except Exception:
                pass

        # ---------------------------------------------------------
        # FALLBACK MATCH: JOB NUMBER
        # ---------------------------------------------------------

        job_number = workflow.get(
            "job_number"
        )

        if job_number:

            job = self.import_jobs.find_one(
                {
                    "job_number": job_number,
                    "is_deleted": {
                        "$ne": True,
                    },
                }
            )

            if job:
                return job

        return None

    def _build_job_row(
        self,
        workflow: dict,
    ) -> dict:

        job = self._find_import_job(
            workflow
        ) or {}

        return {
            "job_number": (
                job.get("job_number")
                or workflow.get("job_number")
                or ""
            ),

            "bl_no": (
                job.get("bl_no")
                or ""
            ),

            "be_no": (
                workflow.get("be_no")
                or ""
            ),

            "consignee_name": (
                job.get("consignee_name")
                or ""
            ),

            "eta": self._format_date(
                job.get("eta")
            ),
        }

    # ---------------------------------------------------------
    # PENDING RULES
    #
    # IMPORTANT:
    # These match the existing frontend Pending dropdown.
    #
    # Initial test:
    # 1. CO Deface Pending
    # 2. Delivery Order Pending
    # 3. Delivery Pending
    # ---------------------------------------------------------

    def _is_co_deface_pending(
        self,
        workflow: dict,
    ) -> bool:

        return (
            self._normalize(
                workflow.get(
                    "co_deface_required"
                )
            )
            == "yes"
            and
            self._normalize(
                workflow.get(
                    "co_deface"
                )
            )
            == "pending"
        )

    def _is_delivery_order_pending(
        self,
        workflow: dict,
    ) -> bool:

        return (
            self._normalize(
                workflow.get(
                    "do_received"
                )
            )
            == "pending"
        )

    def _is_delivery_pending(
        self,
        workflow: dict,
    ) -> bool:

        # Frontend:
        # delivery === "Pending"
        #
        # Backend mapping:
        # detention -> delivery

        return (
            self._normalize(
                workflow.get(
                    "detention"
                )
            )
            == "pending"
        )

    # ---------------------------------------------------------
    # BUILD REPORT
    # ---------------------------------------------------------

    def build_pending_sections(
        self,
    ) -> list[dict]:

        workflows = list(
            self.import_workflows.find(
                {
                    "is_deleted": {
                        "$ne": True,
                    }
                }
            )
        )

        co_deface_jobs: list[dict] = []
        delivery_order_jobs: list[dict] = []
        delivery_jobs: list[dict] = []

        for workflow in workflows:

            if self._is_co_deface_pending(
                workflow
            ):
                co_deface_jobs.append(
                    self._build_job_row(
                        workflow
                    )
                )

            if self._is_delivery_order_pending(
                workflow
            ):
                delivery_order_jobs.append(
                    self._build_job_row(
                        workflow
                    )
                )

            if self._is_delivery_pending(
                workflow
            ):
                delivery_jobs.append(
                    self._build_job_row(
                        workflow
                    )
                )

        sections = []

        if co_deface_jobs:
            sections.append(
                {
                    "title":
                        "CO Deface Pending",

                    "jobs":
                        co_deface_jobs,
                }
            )

        if delivery_order_jobs:
            sections.append(
                {
                    "title":
                        "Delivery Order Pending",

                    "jobs":
                        delivery_order_jobs,
                }
            )

        if delivery_jobs:
            sections.append(
                {
                    "title":
                        "Delivery Pending",

                    "jobs":
                        delivery_jobs,
                }
            )

        return sections

    # ---------------------------------------------------------
    # SEND DAILY REPORT
    # ---------------------------------------------------------

    def send_daily_pending_report(
        self,
    ) -> dict:

        pending_sections = (
            self.build_pending_sections()
        )

        if not pending_sections:
            return {
                "sent": False,
                "message":
                    "No pending jobs found.",
            }

        total_jobs = sum(
            len(
                section.get(
                    "jobs",
                    [],
                )
            )
            for section
            in pending_sections
        )

        email_service.send_pending_jobs_email(
            pending_sections
        )

        return {
            "sent": True,
            "message":
                "Pending jobs email sent successfully.",

            "sections":
                len(pending_sections),

            "total_matches":
                total_jobs,
        }


pending_job_email_service = (
    PendingJobEmailService()
)