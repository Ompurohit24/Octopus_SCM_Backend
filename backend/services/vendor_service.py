from fastapi import HTTPException, status

from backend.models.vendor import VendorCreate, VendorUpdate
from backend.repositories.vendor_repository import vendor_repository


class VendorService:

    def get_next_code(self):
        return {
            "vendor_code": vendor_repository.get_next_code()
        }

    def list(self, search: str, skip: int, limit: int):
        return vendor_repository.search(
            search=search,
            skip=skip,
            limit=limit,
        )


    def get(self, vendor_id: str):
        vendor = vendor_repository.get(vendor_id)

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        return vendor

    def create(self, vendor: VendorCreate):
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

        return vendor_repository.create(vendor.model_dump())

    def update(self, vendor_id: str, vendor: VendorUpdate):
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

        return vendor_repository.update(
            vendor_id,
            vendor.model_dump(exclude_unset=True),
        )

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