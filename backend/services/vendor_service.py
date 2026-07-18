from fastapi import BackgroundTasks, HTTPException, status

from backend.models.vendor import VendorCreate, VendorUpdate
from backend.repositories.vendor_repository import vendor_repository
from backend.repositories.counter_repository import counter_repository
from backend.services.email_service import email_service
from backend.utils.serializer import serialize, serialize_list


class VendorService:

    def get_next_code(self):
        counter = counter_repository.current("vendor")

        return {
            "vendor_code": f"VEN-{counter + 1:04d}"
        }

    def list(self, search: str, skip: int, limit: int):
        vendors = vendor_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )

        return serialize_list(vendors)

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
        duplicate = vendor_repository.find_duplicate(
            vendor_name=vendor.vendor_name,
            gstin=vendor.gstin,
            pan=vendor.pan,
            email=vendor.email,
            phone=vendor.phone,
        )

        if duplicate:
            messages = {
                "vendor_name": "Vendor Name already exists.",
                "gstin": "GSTIN already exists.",
                "pan": "PAN already exists.",
                "email": "Email already exists.",
                "phone": "Mobile Number already exists.",
            }

            raise ValueError(messages[duplicate])

        number = counter_repository.next("vendor")
        vendor_code = f"VEN-{number:04d}"

        document = vendor.model_dump()

        # Never trust the frontend-generated code during creation.
        document["vendor_code"] = vendor_code

        created_vendor = vendor_repository.create(document)

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
        existing = vendor_repository.get(vendor_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        merged = {
            **existing,
            **vendor.model_dump(exclude_unset=True),
        }

        duplicate = vendor_repository.find_duplicate(
            vendor_name=merged["vendor_name"],
            gstin=merged["gstin"],
            pan=merged["pan"],
            email=merged["email"],
            phone=merged["phone"],
            exclude_id=vendor_id,
        )

        if duplicate:
            messages = {
                "vendor_name": "Vendor Name already exists.",
                "gstin": "GSTIN already exists.",
                "pan": "PAN already exists.",
                "email": "Email already exists.",
                "phone": "Mobile Number already exists.",
            }

            raise ValueError(messages[duplicate])

        vendor_repository.update(
            vendor_id,
            vendor.model_dump(exclude_unset=True),
        )

        updated_vendor = vendor_repository.get(vendor_id)

        return serialize(updated_vendor)

    def delete(self, vendor_id: str):
        if not vendor_repository.get(vendor_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        vendor_repository.delete(vendor_id)

        return {
            "message": "Vendor deleted successfully."
        }


vendor_service = VendorService()