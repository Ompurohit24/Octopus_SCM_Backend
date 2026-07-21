from fastapi import BackgroundTasks, HTTPException, status

from backend.models.vendor import VendorCreate, VendorUpdate
from backend.repositories.vendor_repository import vendor_repository
from backend.repositories.counter_repository import counter_repository
from backend.services.email_service import email_service
from backend.utils.serializer import serialize, serialize_list
from backend.repositories.purchase_order_repository import (
    purchase_order_repository,
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

    def get(self, vendor_id: str):
        vendor = vendor_repository.get(vendor_id)

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        return serialize(vendor)

    def create(
        self,
        vendor: VendorCreate,
        background_tasks: BackgroundTasks,
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

        # Never trust frontend-generated code during creation.
        document["vendor_code"] = vendor_code

        created_vendor = vendor_repository.create(
            document
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
    ):
        existing = vendor_repository.get(
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

        vendor_repository.update(
            vendor_id,
            update_data,
        )

        updated_vendor = vendor_repository.get(
            vendor_id
        )

        return serialize(updated_vendor)

    def delete(
            self,
            vendor_id: str,
    ):
        # -------------------------------------------------
        # FIND VENDOR
        # -------------------------------------------------

        vendor = vendor_repository.get(
            vendor_id
        )

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        # -------------------------------------------------
        # PROTECT VENDOR USED BY PURCHASE ORDER
        #
        # Includes Issued and Cancelled POs.
        # Purchase Order history must retain its Vendor.
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SAFE TO DELETE
        # -------------------------------------------------

        vendor_repository.delete(
            vendor_id
        )

        return {
            "message":
                "Vendor deleted successfully."
        }


vendor_service = VendorService()