from fastapi import HTTPException, status

from models.vendor import (
    VendorCreate,
    VendorUpdate,
)
from repositories.vendor_repository import VendorRepository


class VendorService:
    def __init__(self, db):
        self.repository = VendorRepository(db)

    # --------------------------------------------------
    # Next Vendor Code
    # --------------------------------------------------

    def get_next_code(self):
        return {
            "vendor_code": self.repository.get_next_code()
        }

    # --------------------------------------------------
    # List
    # --------------------------------------------------

    def list(
        self,
        search: str,
        skip: int,
        limit: int,
    ):
        total, items = self.repository.list(
            search,
            skip,
            limit,
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items,
        }

    # --------------------------------------------------
    # Get
    # --------------------------------------------------

    def get(self, vendor_id: str):
        vendor = self.repository.get(vendor_id)

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        return vendor

    # --------------------------------------------------
    # Create
    # --------------------------------------------------

    def create(
        self,
        vendor: VendorCreate,
        created_by: str | None = None,
    ):
        duplicate = self.repository.find_duplicate(
            vendor_name=vendor.vendor_name,
            gstin=vendor.gstin,
            pan=vendor.pan,
            email=vendor.email,
            phone=vendor.phone,
        )

        messages = {
            "vendor_name": "Vendor Name already exists.",
            "gstin": "GSTIN already exists.",
            "pan": "PAN already exists.",
            "email": "Email already exists.",
            "phone": "Mobile Number already exists.",
        }

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=messages[duplicate],
            )

        data = vendor.model_dump()
        data["created_by"] = created_by
        data["updated_by"] = created_by

        return self.repository.create(data)

    # --------------------------------------------------
    # Update
    # --------------------------------------------------

    def update(
        self,
        vendor_id: str,
        vendor: VendorUpdate,
        updated_by: str | None = None,
    ):
        existing = self.repository.get(vendor_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        merged = {
            **existing,
            **vendor.model_dump(exclude_unset=True),
        }

        duplicate = self.repository.find_duplicate(
            vendor_name=merged["vendor_name"],
            gstin=merged["gstin"],
            pan=merged["pan"],
            email=merged["email"],
            phone=merged["phone"],
            exclude_id=vendor_id,
        )

        messages = {
            "vendor_name": "Vendor Name already exists.",
            "gstin": "GSTIN already exists.",
            "pan": "PAN already exists.",
            "email": "Email already exists.",
            "phone": "Mobile Number already exists.",
        }

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=messages[duplicate],
            )

        data = vendor.model_dump(exclude_unset=True)
        data["updated_by"] = updated_by

        return self.repository.update(
            vendor_id,
            data,
        )

    # --------------------------------------------------
    # Delete
    # --------------------------------------------------

    def delete(self, vendor_id: str):
        existing = self.repository.get(vendor_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found.",
            )

        self.repository.delete(vendor_id)

        return {
            "message": "Vendor deleted successfully."
        }