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

KYC_ROOT = Path("KYC")
KYC_ROOT.mkdir(exist_ok=True)


class CustomerService:

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
                    code = CustomerService.generate_customer_code(
                        session=session,
                    )

                    document = customer.model_dump()

                    # -------------------------------------------------
                    # CUSTOMER NAME DUPLICATE CHECK
                    # -------------------------------------------------

                    customer_name = document.get("customer_name")

                    if customer_name:
                        existing = customer_repository.find_one(
                            {
                                "customer_name": {
                                    "$regex": f"^{customer_name.strip()}$",
                                    "$options": "i",
                                },
                                "is_deleted": False,
                            }
                        )

                        if existing:
                            raise ValueError(
                                "Customer Name already exists."
                            )

                    # -------------------------------------------------
                    # MULTIPLE EMAIL DUPLICATE CHECK
                    #
                    # Works with:
                    # Old records:
                    #   email: "abc@example.com"
                    #
                    # New records:
                    #   email: [
                    #       "abc@example.com",
                    #       "accounts@example.com"
                    #   ]
                    # -------------------------------------------------

                    emails = document.get("email") or []

                    if isinstance(emails, str):
                        emails = [emails]

                    for email in emails:
                        email_value = str(email).strip()

                        if not email_value:
                            continue

                        existing = customer_repository.find_one(
                            {
                                "email": {
                                    "$regex": f"^{email_value}$",
                                    "$options": "i",
                                },
                                "is_deleted": False,
                            }
                        )

                        if existing:
                            raise ValueError(
                                f"Email {email_value} already exists."
                            )

                    # -------------------------------------------------
                    # OTHER DUPLICATE CHECKS
                    # -------------------------------------------------

                    duplicates = [
                        ("phone", "Phone Number"),
                        ("gstin", "GSTIN"),
                        ("pan", "PAN"),
                        ("tan", "TAN"),
                    ]

                    for field, label in duplicates:
                        value = document.get(field)

                        if not value:
                            continue

                        existing = customer_repository.find_one(
                            {
                                field: value,
                                "is_deleted": False,
                            }
                        )

                        if existing:
                            raise ValueError(
                                f"{label} already exists."
                            )

                    # -------------------------------------------------
                    # KYC DOCUMENTS
                    # -------------------------------------------------

                    gst_path, pan_path = (
                        CustomerService.save_kyc_documents(
                            customer.customer_name,
                            gst_document,
                            pan_document,
                        )
                    )

                    document.update(
                        {
                            "customer_code": code,
                            "is_active": True,
                            "is_deleted": False,
                            "created_by": user_id,
                            "updated_by": user_id,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                            "gst_document": gst_path,
                            "pan_document": pan_path,
                        }
                    )

                    result = customer_repository.create(
                        document,
                        session=session,
                    )

                    document["_id"] = result.inserted_id

        except DuplicateKeyError as e:
            raise ValueError(str(e))

        except Exception:
            raise

        background_tasks.add_task(
            email_service.send_customer_created_email,
            document,
        )

        return serialize(document)

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