from fastapi import APIRouter, HTTPException, Query

from backend.models.vendor import VendorCreate, VendorUpdate
from backend.services.vendor_service import vendor_service

router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)


@router.get("/next-code")
def get_next_vendor_code():
    return vendor_service.get_next_code()


@router.get("")
def list_vendors(
    search: str = "",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
):
    return vendor_service.list(
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/{vendor_id}")
def get_vendor(vendor_id: str):
    return vendor_service.get(vendor_id)


@router.post("")
def create_vendor(vendor: VendorCreate):
    try:
        return vendor_service.create(vendor)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: str,
    vendor: VendorUpdate,
):
    try:
        return vendor_service.update(vendor_id, vendor)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: str):
    return vendor_service.delete(vendor_id)