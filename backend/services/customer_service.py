from datetime import datetime
from pathlib import Path
import shutil

from fastapi import BackgroundTasks
from pymongo.errors import DuplicateKeyError

from backend.database.mongo import client
from backend.models.customer import CustomerCreate, CustomerUpdate
from backend.repositories.counter_repository import counter_repository
from backend.repositories.customer_repository import customer_repository
from backend.services.email_service import email_service
from backend.utils.serializer import serialize, serialize_list
from backend.repositories.import_job_repository import (
    import_job_repository,
)
from pathlib import Path
import shutil

from datetime import datetime

from backend.repositories.pending_registration_repository import (
    pending_registration_repository,
)
KYC_ROOT = Path("KYC")
KYC_ROOT.mkdir(exist_ok=True)


class CustomerService:

    @staticmethod
    def create_from_verified_registration(
            registration: dict,
            user_id: str,
            background_tasks: BackgroundTasks,
    ):
        # -------------------------------------------------
        # SECURITY CHECKS
        # -------------------------------------------------

        if (
                registration.get("entity_type")
                != "customer"
        ):
            raise ValueError(
                "Invalid Customer registration."
            )

        if (
                registration.get("status")
                != "pending"
        ):
            raise ValueError(
                "Customer registration is no longer pending."
            )

        verifications = (
            registration.get(
                "email_verifications",
                {},
            )
        )

        if not verifications:
            raise ValueError(
                "Customer email verification is missing."
            )

        if not all(
                item.get(
                    "verified",
                    False,
                )
                for item
                in verifications.values()
        ):
            raise ValueError(
                "All Customer emails must be verified."
            )

        # -------------------------------------------------
        # PREPARE CUSTOMER DATA
        # -------------------------------------------------

        form_data = dict(
            registration.get(
                "form_data",
                {},
            )
        )

        if not form_data:
            raise ValueError(
                "Pending Customer data is missing."
            )

        # Revalidate pending data before DB insertion.

        customer = CustomerCreate(
            **form_data
        )

        document = (
            customer.model_dump()
        )

        # -------------------------------------------------
        # GENERATE FINAL CUSTOMER CODE
        #
        # Code is generated only after successful OTP.
        # -------------------------------------------------

        code = (
            CustomerService
            .generate_customer_code()
        )

        document[
            "customer_code"
        ] = code

        # -------------------------------------------------
        # MOVE KYC DOCUMENTS
        #
        # Pending:
        # KYC/Pending/Customer/<registration_id>/GST.pdf
        #
        # Final:
        # KYC/<Customer Name>/GST.pdf
        #
        # Keep the same final Customer KYC structure already
        # used by the existing application.
        # -------------------------------------------------

        temporary_documents = (
            registration.get(
                "temporary_documents",
                {},
            )
        )

        final_folder = (
                Path("KYC")
                / customer.customer_name
        )

        final_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        gst_final_path = None
        pan_final_path = None

        gst_temp = (
            temporary_documents.get(
                "gst_document"
            )
        )

        if gst_temp:
            source = Path(
                gst_temp
            )

            if source.exists():
                destination = (
                        final_folder
                        / f"GST{source.suffix}"
                )

                shutil.move(
                    str(source),
                    str(destination),
                )

                gst_final_path = str(
                    destination
                )

        pan_temp = (
            temporary_documents.get(
                "pan_document"
            )
        )

        if pan_temp:
            source = Path(
                pan_temp
            )

            if source.exists():
                destination = (
                        final_folder
                        / f"PAN{source.suffix}"
                )

                shutil.move(
                    str(source),
                    str(destination),
                )

                pan_final_path = str(
                    destination
                )

        now = datetime.utcnow()

        document.update(
            {
                "is_active":
                    True,

                "is_deleted":
                    False,

                "created_by":
                    user_id,

                "updated_by":
                    user_id,

                "created_at":
                    now,

                "updated_at":
                    now,

                "gst_document":
                    gst_final_path,

                "pan_document":
                    pan_final_path,
            }
        )

        # -------------------------------------------------
        # CREATE CUSTOMER
        # -------------------------------------------------

        created = (
            customer_repository.create(
                document
            )
        )

        if not created:
            raise ValueError(
                "Unable to create Customer."
            )

        # -------------------------------------------------
        # MARK PENDING REGISTRATION COMPLETED
        # -------------------------------------------------

        customer_id = str(
            created.get(
                "_id"
            )
        )

        result = (
            pending_registration_repository
            .mark_completed(
                registration_id=
                registration[
                    "registration_id"
                ],

                entity_id=
                customer_id,
            )
        )

        if not result.modified_count:
            # Customer exists at this point, so do not
            # attempt another Customer insertion.
            raise ValueError(
                "Customer was created but registration "
                "completion could not be recorded."
            )

        # -------------------------------------------------
        # CUSTOMER CREATED EMAIL
        #
        # Runs only after OTP verification + creation.
        # -------------------------------------------------

        background_tasks.add_task(
            email_service
            .send_customer_created_email,

            created,
        )

        return serialize(
            created
        )

    @staticmethod
    def generate_customer_code(session=None):
        number = counter_repository.next(
            "customer",
            session=session,
        )
        return f"CUS-{number:04d}"

    @staticmethod
    def get_next_customer_code():
        counter = counter_repository.current("customer")

        return f"CUS-{counter + 1:04d}"

    @staticmethod
    def save_kyc_documents(
        customer_name: str,
        gst_document,
        pan_document,
    ):
        customer_folder = KYC_ROOT / customer_name
        customer_folder.mkdir(parents=True, exist_ok=True)

        gst_path = None
        pan_path = None

        if gst_document:
            extension = Path(gst_document.filename).suffix
            gst_path = customer_folder / f"GST{extension}"

            with open(gst_path, "wb") as buffer:
                shutil.copyfileobj(gst_document.file, buffer)

        if pan_document:
            extension = Path(pan_document.filename).suffix
            pan_path = customer_folder / f"PAN{extension}"

            with open(pan_path, "wb") as buffer:
                shutil.copyfileobj(pan_document.file, buffer)

        return (
            str(gst_path) if gst_path else None,
            str(pan_path) if pan_path else None,
        )

    @staticmethod
    def create(
            customer: CustomerCreate,
            user_id: str,
            background_tasks: BackgroundTasks,
            gst_document=None,
            pan_document=None,
    ):
        try:
            with client.start_session() as session:
                with session.start_transaction():
                    # -----------------------------------------
                    # GENERATE UNIQUE CUSTOMER CODE
                    # -----------------------------------------

                    code = (
                        CustomerService
                        .generate_customer_code(
                            session=session,
                        )
                    )

                    document = (
                        customer.model_dump()
                    )

                    # -----------------------------------------
                    # KYC DOCUMENTS
                    # -----------------------------------------

                    gst_path, pan_path = (
                        CustomerService
                        .save_kyc_documents(
                            customer.customer_name,
                            gst_document,
                            pan_document,
                        )
                    )

                    # -----------------------------------------
                    # BUILD CUSTOMER DOCUMENT
                    # -----------------------------------------

                    document.update(
                        {
                            "customer_code": code,

                            "is_active": True,
                            "is_deleted": False,

                            "created_by": user_id,
                            "updated_by": user_id,
                            "created_at":
                            datetime.utcnow(),
                            "updated_at":
                                datetime.utcnow(),

                            "gst_document":
                                gst_path,

                            "pan_document":
                                pan_path,
                        }
                    )

                    # -----------------------------------------
                    # CREATE CUSTOMER
                    # -----------------------------------------

                    created = (
                        customer_repository
                        .create(
                            document,
                            session=session,
                        )
                    )

                    if not created:
                        raise ValueError(
                            "Unable to create Customer."
                        )

                    document = created

        except DuplicateKeyError as e:
            # customer_code remains permanently unique.
            raise ValueError(
                str(e)
            )

        except Exception:
            raise

        # ---------------------------------------------
        # CUSTOMER CREATED EMAIL
        # ---------------------------------------------

        background_tasks.add_task(
            email_service
            .send_customer_created_email,
            document,
        )

        return serialize(
            document
        )
    @staticmethod
    def get_all(
        skip: int = 0,
        limit: int = 20,
        search: str = "",
    ):
        customers = customer_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": customer_repository.count(
                {
                    "is_deleted": False
                }
            ),
            "skip": skip,
            "limit": limit,
            "items": serialize_list(customers),
        }

    @staticmethod
    def get_by_id(customer_id: str):
        customer = customer_repository.find_by_id(customer_id)

        if not customer:
            raise ValueError("Customer not found")

        return serialize(customer)

    @staticmethod
    def update(
        customer_id: str,
        customer: CustomerUpdate,
    ):
        data = customer.model_dump(exclude_unset=True)

        data["updated_at"] = datetime.utcnow()

        customer_repository.update(
            customer_id,
            data,
        )

        updated = customer_repository.find_by_id(customer_id)

        return serialize(updated)

    @staticmethod
    def delete(customer_id: str):

        customer = customer_repository.find_by_id(
            customer_id
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        customer_name = (
            customer.get("customer_name", "")
            .strip()
        )

        linked_job = (
            import_job_repository.find_active_by_customer(
                customer_name=customer_name,
            )
        )

        if linked_job:
            job_number = linked_job.get(
                "job_number",
                "Unknown Job",
            )

            raise ValueError(
                f"Cannot delete this Customer. "
                f"This Customer is linked to Import Job "
                f"{job_number}. "
                f"Delete the Import Job first before "
                f"deleting this Customer."
            )

        customer_repository.soft_delete(
            customer_id
        )

        return {
            "message": "Customer deleted successfully"
        }