from datetime import datetime

from backend.models.import_workflow import (
    ImportWorkflowCreate,
    ImportWorkflowUpdate,
)
from backend.repositories.import_job_repository import import_job_repository
from backend.repositories.import_workflow_repository import (
    import_workflow_repository,
)
from backend.services.import_workflow_history_service import (
    import_workflow_history_service,
)
from backend.utils.serializer import serialize, serialize_list


class ImportWorkflowService:

    STAGES = [
        "checklist",
        "igm",
        "igm_status",
        "inward_date",
        "be_no",
        "be_date",
        "goods_registration",
        "other_gov_agency",
        "assessment_type",
        "boe_copy_mailed",
        "original_documents",
        "co_deface_required",
        "duty_payment",
        "out_of_charge",
        "oc_mail_sent",
        "liner_invoice_received",
        "liner_payment",
        "payment_confirmation",
        "do_received",
        "transportation",
        "empty_container_return",
        "container_unloaded",
        "detention",
        "job_closed",
    ]

    @staticmethod
    def create(
        job_id: str,
        workflow: ImportWorkflowCreate,
        user_id: str,
    ):

        existing = import_workflow_repository.find_by_job_id(job_id)

        if existing:
            raise ValueError("Workflow already exists.")

        job = import_job_repository.find_by_id(job_id)

        if not job:
            raise ValueError("Import Job not found.")

        document = workflow.model_dump()

        document.update(
            {
                "job_id": job_id,
                "job_number": job["job_number"],
                "party_name": job["forwarder"],
                "bl_no": job["bl_no"],
                "containers": f'{job["no_of_cntr"]} x {job["size"]}',
                "current_stage": "checklist",
                "is_active": True,
                "is_deleted": False,
                "created_by": user_id,
                "updated_by": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        result = import_workflow_repository.create(document)

        document["_id"] = result.inserted_id

        return serialize(document)

    @staticmethod
    def get(job_id: str):

        job = import_job_repository.find_by_id(job_id)

        if not job:
            raise ValueError("Import Job not found.")

        workflow = import_workflow_repository.find_by_job_id(job_id)

        if not workflow:
            empty_workflow = {
                "current_stage": "checklist",
            }

            return {
                "job": {
                    "id": str(job["_id"]),
                    "job_number": job["job_number"],
                    "party": job["forwarder"],
                    "bl_no": job["bl_no"],
                    "containers": f'{job["no_of_cntr"]} x {job["size"]}',
                },
                "workflow": None,
                "current_stage": "checklist",
                "next_stage": "checklist",
                "progress": 0,
                "field_access": ImportWorkflowService.get_field_access(
                    empty_workflow
                ),
            }

        return {
            "job": {
                "id": str(job["_id"]),
                "job_number": job["job_number"],
                "party": job["forwarder"],
                "bl_no": job["bl_no"],
                "containers": f'{job["no_of_cntr"]} x {job["size"]}',
            },
            "workflow": serialize(workflow),
            "current_stage": workflow["current_stage"],
            "next_stage": workflow["current_stage"],
            "progress": ImportWorkflowService.calculate_progress(
                workflow
            ),
            "field_access": ImportWorkflowService.get_field_access(
                workflow
            ),
        }

    @staticmethod
    def update(
        job_id: str,
        workflow: ImportWorkflowUpdate,
        user_id: str,
    ):
        print("===== UPDATE METHOD CALLED =====")
        existing = import_workflow_repository.find_by_job_id(job_id)

        if not existing:
            raise ValueError("Workflow not found.")

        # data = workflow.model_dump(exclude_unset=True)

        data = workflow.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        print("========== MODEL DUMP ==========")
        print(data)

        # -------------------------------------------------
        # SERVICE MAP CLEANUP
        # -------------------------------------------------
        # These fields must be replaced completely when
        # services are selected/unselected in Update Job.
        #
        # Example:
        #
        # Existing:
        # {
        #     "FSSAI": {...},
        #     "CDRUG": {...}
        # }
        #
        # Incoming:
        # {
        #     "FSSAI": {...}
        # }
        #
        # Result must NOT retain CDRUG.
        # -------------------------------------------------

        SERVICE_FIELDS = {
            "other_gov_agency_type",
            "other_services",
        }

        for field in SERVICE_FIELDS:

            if field not in data:
                continue

            value = data[field]

            if not isinstance(value, dict):
                data[field] = {}
                continue

            cleaned = {}

            for service_name, service_data in value.items():

                # Ignore legacy numeric keys:
                # "0", "1", "2", etc.
                if str(service_name).isdigit():
                    continue

                if service_data is None:
                    continue

                cleaned[service_name] = service_data

            data[field] = cleaned

        # Remove empty strings from normal fields,
        # but NEVER remove service fields.
        data = {
            key: value
            for key, value in data.items()
            if (
                    key in SERVICE_FIELDS
                    or value != ""
            )
        }

        from backend.utils.import_workflow_validator import (
            ImportWorkflowValidator,
        )

        import pprint

        merged = {
            **existing,
            **data,
        }

        print("\n================ EXISTING ================")
        pprint.pprint(existing)

        print("\n================ DATA ====================")
        pprint.pprint(data)

        print("\n================ MERGED ==================")
        pprint.pprint(merged)

        print("========== MERGED ==========")
        print("igm_status =", merged.get("igm_status"))
        print("igm_no =", merged.get("igm_no"))
        print("igm_date =", merged.get("igm_date"))

        import pprint

        print("\n========== OTHER GOV AGENCY ==========")
        pprint.pprint(merged.get("other_gov_agency_type"))

        ImportWorkflowValidator.validate(merged)

        data["updated_by"] = user_id
        data["updated_at"] = datetime.utcnow()

        stage = ImportWorkflowService.find_current_stage(
            {
                **existing,
                **data,
            }
        )

        import_workflow_history_service.log_changes(
            workflow=existing,
            updated_data=data,
            user_id=user_id,
        )

        import_workflow_repository.update_stage(
            job_id=job_id,
            stage=stage,
            data=data,
        )

        job_update = {}

        if "be_no" in data:
            job_update["be_no"] = data["be_no"]

        if job_update:
            import_job_repository.update(
                job_id,
                job_update,
            )

        updated = import_workflow_repository.find_by_job_id(job_id)
        print("job_id:", job_id)
        print("job_update:", job_update)

        result = import_job_repository.update(
            job_id,
            job_update,
        )

        print("matched:", result.matched_count)
        print("modified:", result.modified_count)

        return serialize(updated)



    @staticmethod
    def delete(job_id: str):

        workflow = import_workflow_repository.find_by_job_id(job_id)

        if not workflow:
            raise ValueError("Workflow not found.")

        import_workflow_repository.soft_delete(workflow["_id"])

        return {
            "message": "Workflow deleted successfully."
        }

    @staticmethod
    def search(
        search: str = "",
        skip: int = 0,
        limit: int = 20,
    ):

        workflows = import_workflow_repository.search_jobs(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": import_workflow_repository.count(
                {
                    "is_deleted": False,
                }
            ),
            "skip": skip,
            "limit": limit,
            "items": serialize_list(workflows),
        }

    @staticmethod
    def find_current_stage(data: dict):

        if data.get("checklist") != "Done":
            return "checklist"

        if not data.get("igm_no"):
            return "igm"

        if data.get("igm_status") != "Done":
            return "igm_status"

        if not data.get("inward_date"):
            return "inward_date"

        if not data.get("be_no"):
            return "be_no"

        if not data.get("be_date"):
            return "be_date"

        if data.get("goods_registration") != "Done":
            return "goods_registration"

        if (
            data.get("other_gov_agency") == "Yes"
            and not data.get("other_gov_agency_type")
        ):
            return "other_gov_agency"

        if (
            data.get("assessment_type") == "APR"
            and not data.get("cfs_name")
        ):
            return "assessment_type"

        if data.get("boe_copy_mailed") != "Done":
            return "boe_copy_mailed"

        if data.get("original_documents") != "Done":
            return "original_documents"

        if (
            data.get("co_deface_required") == "Yes"
            and data.get("co_deface") != "Done"
        ):
            return "co_deface_required"

        if data.get("duty_payment") != "Done":
            return "duty_payment"

        if data.get("out_of_charge") != "Done":
            return "out_of_charge"

        if data.get("oc_mail_sent") != "Done":
            return "oc_mail_sent"

        if data.get("liner_invoice_received") != "Done":
            return "liner_invoice_received"

        if data.get("liner_payment") != "Done":
            return "liner_payment"

        if data.get("payment_confirmation") != "Done":
            return "payment_confirmation"

        if data.get("do_received") == "Done":

            if not data.get("do_validity"):
                return "do_received"

            if not data.get("do_type"):
                return "do_received"

        if (
            data.get("transportation") == "Octopus"
            and not data.get("transporter")
        ):
            return "transportation"

        if data.get("empty_container_return") != "Done":
            return "empty_container_return"

        if data.get("container_unloaded") != "Done":
            return "container_unloaded"

        if data.get("detention") != "Done":
            return "detention"

        return "job_closed"

    @staticmethod
    def search_jobs(
            search: str = "",
            skip: int = 0,
            limit: int = 20,
    ):

        jobs = import_job_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        items = []

        for job in jobs:
            items.append(
                {
                    "id": str(job["_id"]),
                    "job_number": job["job_number"],
                    "bl_no": job["bl_no"],
                    "be_no": job.get("be_no"),
                    "party": job["forwarder"],
                    "containers": f'{job["no_of_cntr"]} x {job["size"]}',
                }
            )

        return {
            "total": import_job_repository.count(
                {
                    "is_deleted": False,
                }
            ),
            "skip": skip,
            "limit": limit,
            "items": items,
        }

    @staticmethod
    def calculate_progress(workflow: dict):

        total = len(
            ImportWorkflowService.STAGES
        )

        completed = 0

        current = workflow.get(
            "current_stage",
            "checklist",
        )

        if current in ImportWorkflowService.STAGES:
            completed = (
                ImportWorkflowService.STAGES.index(
                    current
                )
            )

        return round(
            (completed / total) * 100
        )

    @staticmethod
    def get_field_access(workflow: dict):

        enabled = []
        disabled = []

        fields = [
            "checklist",
            "igm_no",
            "igm_date",
            "igm_status",
            "inward_date",
            "be_no",
            "be_date",
            "goods_registration",
            "other_gov_agency",
            "other_gov_agency_type",
            "assessment_type",
            "cfs_name",
            "boe_copy_mailed",
            "original_documents",
            "co_deface_required",
            "co_deface",
            "duty_payment",
            "out_of_charge",
            "oc_mail_sent",
            "liner_invoice_received",
            "liner_payment",
            "payment_confirmation",
            "do_received",
            "do_validity",
            "do_type",
            "transportation",
            "transporter",
            "empty_container_return",
            "container_unloaded",
            "detention",
            "job_closed",
        ]

        current = workflow.get(
            "current_stage",
            "checklist",
        )

        passed = False

        for field in fields:

            if field == current:
                passed = True

            if not passed:
                disabled.append(field)
            else:
                enabled.append(field)

        return {
            "enabled_fields": enabled,
            "disabled_fields": disabled,
        }
