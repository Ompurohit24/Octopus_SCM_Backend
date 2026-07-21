from datetime import datetime
from backend.database.mongo import client
from backend.models.import_job import ImportJobCreate, ImportJobUpdate
from backend.repositories.counter_repository import counter_repository
from backend.repositories.import_job_repository import import_job_repository
from backend.utils.serializer import serialize, serialize_list
from backend.repositories.customer_repository import customer_repository
from backend.services.email_service import email_service
from backend.repositories.import_workflow_repository import (
    import_workflow_repository,
)

from backend.repositories.purchase_order_repository import (
    purchase_order_repository,
)
class ImportJobService:

    @staticmethod
    def generate_job_number():
        number = counter_repository.next("import_job")
        return f"IMP-{number:05d}"

    @staticmethod
    def get_next_job_number():

        counter = counter_repository.current("import_job")

        return f"IMP-{counter + 1:05d}"

    @staticmethod
    def create(job: ImportJobCreate, user_id: str):

        existing_job = import_job_repository.find_by_bl_no(job.bl_no)

        if existing_job:
            raise ValueError(
                f"Import Job already exists for BL No '{job.bl_no}'."
            )

        job_number = ImportJobService.generate_job_number()

        customer = customer_repository.find_by_name(job.forwarder)

        if not customer:
            raise ValueError("Forwarder not found")

        document = job.model_dump()

        document["forwarder_name"] = customer["customer_name"]

        document.update(
            {
                "job_number": job_number,
                "is_active": True,
                "is_deleted": False,
                "created_by": user_id,
                "updated_by": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        # Create Import Job
        created = import_job_repository.create(document)

        # BaseRepository.create() returns the created document,
        # not PyMongo InsertOneResult.
        job_id = str(created["_id"])

        # Automatically create Import Workflow
        workflow = {
            "job_id": job_id,
            "job_number": job_number,
            "party_name": customer["customer_name"],
            "bl_no": job.bl_no,
            "containers": f"{job.no_of_cntr} x {job.size}",

            "checklist": "Pending",
            "igm_status": "Pending",
            "goods_registration": "Pending",
            "boe_copy_mailed": "Pending",
            "original_documents": "Pending",
            "duty_payment": "Pending",
            "out_of_charge": "Pending",
            "oc_mail_sent": "Pending",
            "liner_invoice_received": "Pending",
            "liner_payment": "Pending",
            "payment_confirmation": "Pending",
            "empty_container_return": "Pending",
            "container_unloaded": "Pending",
            "detention": "Pending",
            "job_closed": "Pending",

            "current_stage": "checklist",

            "is_active": True,
            "is_deleted": False,

            "created_by": user_id,
            "updated_by": user_id,

            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        import_workflow_repository.create(workflow)

        # Send Import Job created email
        try:
            email_service.send_import_job_created_email(
                customer["email"],
                created,
            )
        except Exception as e:
            print(
                "Import job created email failed:",
                e,
            )

        return serialize(created)

    @staticmethod
    def get_all(
        skip: int = 0,
        limit: int = 20,
        search: str = "",
    ):

        jobs = import_job_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": import_job_repository.count(
                {
                    "is_deleted": False
                }
            ),
            "skip": skip,
            "limit": limit,
            "items": serialize_list(jobs),
        }

    @staticmethod
    def get_by_id(job_id: str):

        job = import_job_repository.find_by_id(job_id)

        if not job:
            raise ValueError("Import Job not found")

        return serialize(job)

    @staticmethod
    def update(
        job_id: str,
        job: ImportJobUpdate,
    ):

        data = job.model_dump(exclude_unset=True)

        data["updated_at"] = datetime.utcnow()

        import_job_repository.update(
            job_id,
            data,
        )

        updated = import_job_repository.find_by_id(job_id)

        return serialize(updated)

    @staticmethod
    def delete(job_id: str):

        # -------------------------------------------------
        # VALIDATE IMPORT JOB
        # -------------------------------------------------

        job = import_job_repository.find_by_id(
            job_id
        )

        if not job:
            raise ValueError(
                "Import Job not found"
            )

        # -------------------------------------------------
        # BLOCK DELETE WHEN AN ISSUED PO EXISTS
        #
        # Never silently delete an operational job while
        # there is an active vendor commitment.
        # -------------------------------------------------

        issued_po = (
            purchase_order_repository
            .get_issued_by_job_id(
                job_id=job_id,
            )
        )

        if issued_po:
            po_number = issued_po.get(
                "po_number",
                "Unknown PO",
            )

            service_name = issued_po.get(
                "service_name",
                "Unknown Service",
            )

            vendor_name = issued_po.get(
                "vendor_name",
                "Unknown Vendor",
            )

            raise ValueError(
                f"Cannot delete this Import Job. "
                f"Active Purchase Order {po_number} "
                f"for {service_name} is assigned to "
                f"{vendor_name}. Cancel all active "
                f"Purchase Orders before deleting the job."
            )

        # -------------------------------------------------
        # TRANSACTIONAL SOFT DELETE
        # -------------------------------------------------

        with client.start_session() as session:

            with session.start_transaction():
                job_result = (
                    import_job_repository
                    .soft_delete_by_id(
                        job_id=job_id,
                        session=session,
                    )
                )

                if job_result.modified_count == 0:
                    raise ValueError(
                        "Import Job not found "
                        "or already deleted"
                    )

                (
                    import_workflow_repository
                    .soft_delete_by_job_id(
                        job_id=job_id,
                        session=session,
                    )
                )

        return {
            "message":
                "Import Job deleted successfully"
        }