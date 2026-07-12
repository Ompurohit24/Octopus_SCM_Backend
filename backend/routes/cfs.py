from fastapi import APIRouter, Depends

from backend.models.cfs import CFSCreate, CFSUpdate
from backend.services.cfs_service import cfs_service
from backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/cfs",
    tags=["CFS"],
)


@router.post("")
def create_cfs(
    cfs: CFSCreate,
    user=Depends(get_current_user),
):
    return cfs_service.create(
        cfs,
        user["sub"],
    )


@router.get("")
def get_cfs(
    search: str = "",
    skip: int = 0,
    limit: int = 50,
):
    return cfs_service.get_all(
        search,
        skip,
        limit,
    )


@router.put("/{cfs_id}")
def update_cfs(
    cfs_id: str,
    cfs: CFSUpdate,
):
    return cfs_service.update(
        cfs_id,
        cfs,
    )


@router.delete("/{cfs_id}")
def delete_cfs(
    cfs_id: str,
):
    return cfs_service.delete(cfs_id)