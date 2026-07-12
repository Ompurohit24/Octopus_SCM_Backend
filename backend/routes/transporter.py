from fastapi import APIRouter, Depends

from backend.models.transporter import (
    TransporterCreate,
    TransporterUpdate,
)
from backend.services.transporter_service import (
    transporter_service,
)
from backend.utils.dependencies import (
    get_current_user,
)

router = APIRouter(
    prefix="/transporters",
    tags=["Transporters"],
)


@router.post("")
def create(
    transporter: TransporterCreate,
    user=Depends(get_current_user),
):
    return transporter_service.create(
        transporter,
        user["sub"],
    )


@router.get("")
def get_all(
    search: str = "",
    skip: int = 0,
    limit: int = 50,
):
    return transporter_service.get_all(
        search,
        skip,
        limit,
    )


@router.put("/{transporter_id}")
def update(
    transporter_id: str,
    transporter: TransporterUpdate,
):
    return transporter_service.update(
        transporter_id,
        transporter,
    )


@router.delete("/{transporter_id}")
def delete(
    transporter_id: str,
):
    return transporter_service.delete(
        transporter_id,
    )