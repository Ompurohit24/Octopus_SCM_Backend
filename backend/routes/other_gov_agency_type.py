from fastapi import APIRouter, Depends

from backend.models.other_gov_agency_type import (
    OtherGovAgencyTypeCreate,
    OtherGovAgencyTypeUpdate,
)
from backend.services.other_gov_agency_type_service import (
    other_gov_agency_type_service,
)
from backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/other-gov-agency-types",
    tags=["Other Gov Agency Types"],
)


@router.post("")
def create(
    data: OtherGovAgencyTypeCreate,
    user=Depends(get_current_user),
):
    return other_gov_agency_type_service.create(
        data,
        user["sub"],
    )


@router.get("")
def get_all(
    search: str = "",
    skip: int = 0,
    limit: int = 50,
):
    return other_gov_agency_type_service.get_all(
        search,
        skip,
        limit,
    )


@router.put("/{item_id}")
def update(
    item_id: str,
    data: OtherGovAgencyTypeUpdate,
):
    return other_gov_agency_type_service.update(
        item_id,
        data,
    )


@router.delete("/{item_id}")
def delete(
    item_id: str,
):
    return other_gov_agency_type_service.delete(
        item_id,
    )