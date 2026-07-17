from fastapi import APIRouter, Depends, Query

from core.database import get_database
from models.vendor import VendorCreate, VendorUpdate
from services.vendor_service import VendorService

router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)


def get_service():
    db = get_database()
    return VendorService(db)


@router.get("/next-code")
def get_next_vendor_code(
    service: VendorService = Depends(get_service),
):
    return service.get_next_code()


@router.get("")
def list_vendors(
    search: str = "",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
    service: VendorService = Depends(get_service),
):
    return service.list(
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: str,
    service: VendorService = Depends(get_service),
):
    return service.get(vendor_id)


@router.post("")
def create_vendor(
    vendor: VendorCreate,
    service: VendorService = Depends(get_service),
):
    return service.create(vendor)


@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: str,
    vendor: VendorUpdate,
    service: VendorService = Depends(get_service),
):
    return service.update(
        vendor_id,
        vendor,
    )


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: str,
    service: VendorService = Depends(get_service),
):
    return service.delete(vendor_id)