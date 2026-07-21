
from pathlib import Path
import shutil

from fastapi import (
    BackgroundTasks,
    HTTPException,
    status,
)
from backend.models.vendor import VendorCreate, VendorUpdate
from backend.repositories.vendor_repository import vendor_repository
from backend.repositories.counter_repository import counter_repository
from backend.services.email_service import email_service
from backend.utils.serializer import serialize, serialize_list
from backend.repositories.purchase_order_repository import (
    purchase_order_repository,
)

KYC_ROOT = Path("KYC") / "Vendor"
KYC_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)

class VendorService:

    def get_next_code(self):
        counter = counter_repository.current("vendor")

        return {
            "vendor_code": f"VEN-{counter + 1:04d}"
        }

    def list(
        self,
        search: str,
        skip: int,
        limit: int,
    ):
        vendors = vendor_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return {
            "total": vendor_repository.count(
                {
                    "is_deleted": False
                }
            ),
            "skip": skip,
            "limit": limit,
            "items": serialize_list(vendors),
        }

    def get(
            self,
            vendor_id: str,
    ):
        vendor = (
            vendor_repository.find_by_id(
                vendor_id
            )
        )

        if not vendor:
            raise HTTPException(
                status_code=
                status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        return serialize(vendor)

    @staticmethod
    def save_kyc_documents(
            vendor_name: str,
            gst_document=None,
            pan_document=None,
    ):
        vendor_folder = (
                KYC_ROOT / vendor_name
        )

        vendor_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        gst_path = None
        pan_path = None

        if gst_document:
            extension = Path(
                gst_document.filename
            ).suffix

            gst_path = (
                    vendor_folder
                    / f"GST{extension}"
            )

            with open(
                    gst_path,
                    "wb",
            ) as buffer:
                shutil.copyfileobj(
                    gst_document.file,
                    buffer,
                )

        if pan_document:
            extension = Path(
                pan_document.filename
            ).suffix

            pan_path = (
                    vendor_folder
                    / f"PAN{extension}"
            )

            with open(
                    pan_path,
                    "wb",
            ) as buffer:
                shutil.copyfileobj(
                    pan_document.file,
                    buffer,
                )

        return (
            str(gst_path)
            if gst_path
            else None,

            str(pan_path)
            if pan_path
            else None,
        )

    def create(
            self,
            vendor: VendorCreate,
            background_tasks: BackgroundTasks,
            gst_document=None,
            pan_document=None,
    ):
        # -------------------------------------------------
        # NORMALIZE EMAILS
        # -------------------------------------------------

        emails = vendor.email or []

        # Extra backward compatibility in case this service
        # is ever called without Pydantic normalization.
        if isinstance(emails, str):
            emails = [emails]

        # -------------------------------------------------
        # CHECK NON-EMAIL DUPLICATES
        # -------------------------------------------------

        duplicate = vendor_repository.find_duplicate(
            vendor_name=vendor.vendor_name,
            gstin=vendor.gstin,
            pan=vendor.pan,
            email=None,
            phone=vendor.phone,
        )

        if duplicate:
            messages = {
                "vendor_name":
                    "Vendor Name already exists.",
                "gstin":
                    "GSTIN already exists.",
                "pan":
                    "PAN already exists.",
                "phone":
                    "Mobile Number already exists.",
            }

            raise ValueError(
                messages.get(
                    duplicate,
                    "Vendor already exists.",
                )
            )

        # -------------------------------------------------
        # CHECK EVERY EMAIL
        #
        # Works against:
        #
        # Old MongoDB:
        # email: "vendor@example.com"
        #
        # New MongoDB:
        # email: [
        #     "vendor@example.com",
        #     "accounts@example.com"
        # ]
        # -------------------------------------------------

        for email in emails:
            email_value = str(email).strip()

            if not email_value:
                continue

            duplicate = vendor_repository.find_duplicate(
                email=email_value,
            )

            if duplicate == "email":
                raise ValueError(
                    f"Email {email_value} already exists."
                )

        # -------------------------------------------------
        # GENERATE VENDOR CODE
        # -------------------------------------------------

        number = counter_repository.next("vendor")
        vendor_code = f"VEN-{number:04d}"

        document = vendor.model_dump()

        # Never trust frontend-generated code
        # during creation.
        document["vendor_code"] = (
            vendor_code
        )

        # -----------------------------------------
        # SAVE GST + PAN DOCUMENTS
        # -----------------------------------------

        gst_path, pan_path = (
            self.save_kyc_documents(
                vendor_name=vendor.vendor_name,
                gst_document=gst_document,
                pan_document=pan_document,
            )
        )

        document[
            "gst_document"
        ] = gst_path

        document[
            "pan_document"
        ] = pan_path

        # -----------------------------------------
        # CREATE VENDOR
        # -----------------------------------------

        created_vendor = (
            vendor_repository.create(
                document
            )
        )

        background_tasks.add_task(
            email_service.send_vendor_created_email,
            created_vendor,
        )

        return serialize(created_vendor)

    def update(
            self,
            vendor_id: str,
            vendor: VendorUpdate,
            gst_document=None,
            pan_document=None,
    ):
        existing = vendor_repository.find_by_id(
            vendor_id
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        update_data = vendor.model_dump(
            exclude_unset=True
        )

        merged = {
            **existing,
            **update_data,
        }

        # -------------------------------------------------
        # CHECK NON-EMAIL DUPLICATES
        # -------------------------------------------------

        duplicate = vendor_repository.find_duplicate(
            vendor_name=merged.get("vendor_name"),
            gstin=merged.get("gstin"),
            pan=merged.get("pan"),
            email=None,
            phone=merged.get("phone"),
            exclude_id=vendor_id,
        )

        if duplicate:
            messages = {
                "vendor_name":
                    "Vendor Name already exists.",
                "gstin":
                    "GSTIN already exists.",
                "pan":
                    "PAN already exists.",
                "phone":
                    "Mobile Number already exists.",
            }

            raise ValueError(
                messages.get(
                    duplicate,
                    "Vendor already exists.",
                )
            )

        # -------------------------------------------------
        # CHECK EVERY EMAIL ON UPDATE
        # -------------------------------------------------

        emails = merged.get("email") or []

        if isinstance(emails, str):
            emails = [emails]

        for email in emails:
            email_value = str(email).strip()

            if not email_value:
                continue

            duplicate = vendor_repository.find_duplicate(
                email=email_value,
                exclude_id=vendor_id,
            )

            if duplicate == "email":
                raise ValueError(
                    f"Email {email_value} already exists."
                )

        # -------------------------------------------------
        # UPDATE
        # -------------------------------------------------

        # -------------------------------------------------
        # UPDATE KYC DOCUMENTS
        #
        # If no new document is uploaded,
        # existing document path remains unchanged.
        # -------------------------------------------------

        vendor_name = merged.get(
            "vendor_name"
        )

        if gst_document:
            gst_path, _ = (
                self.save_kyc_documents(
                    vendor_name=vendor_name,
                    gst_document=gst_document,
                    pan_document=None,
                )
            )

            update_data[
                "gst_document"
            ] = gst_path

        if pan_document:
            _, pan_path = (
                self.save_kyc_documents(
                    vendor_name=vendor_name,
                    gst_document=None,
                    pan_document=pan_document,
                )
            )

            update_data[
                "pan_document"
            ] = pan_path


        vendor_repository.update(
            vendor_id,
            update_data,
        )

        updated_vendor = vendor_repository.find_by_id(
            vendor_id
        )

        return serialize(updated_vendor)

    def delete(
            self,
            vendor_id: str,
    ):
        vendor = vendor_repository.find_by_id(
            vendor_id
        )

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        linked_po = (
            purchase_order_repository
            .get_any_by_vendor_id(
                vendor_id=vendor_id,
            )
        )

        if linked_po:
            po_number = linked_po.get(
                "po_number",
                "Unknown PO",
            )

            raise ValueError(
                f"Cannot delete this Vendor. "
                f"This Vendor is linked to Purchase Order "
                f"{po_number}. "
                f"Vendor cannot be deleted because "
                f"Purchase Order history must be retained."
            )

        vendor_repository.soft_delete(
            vendor_id
        )

        return {
            "message": "Vendor deleted successfully."
        }

vendor_service = VendorService()