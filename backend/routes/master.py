from fastapi import APIRouter

from backend.services.dropdown_service import dropdown_service

router = APIRouter(
    prefix="/masters",
    tags=["Masters"],
)


@router.get("/cfs")
def get_cfs(
    search: str = "",
):
    return dropdown_service.get_cfs(search)


@router.get("/transporters")
def get_transporters(
    search: str = "",
):
    return dropdown_service.get_transporters(search)


@router.get("/other-gov-agency-types")
def get_other_gov_agency_types(
    search: str = "",
):
    return dropdown_service.get_other_gov_agency_types(
        search
    )


@router.get("/assessment-types")
def get_assessment_types():
    return [
        "RMS",
        "APR",
    ]


@router.get("/do-types")
def get_do_types():
    return [
        "Factory",
        "Doc destuff",
    ]


@router.get("/do-processes")
def get_do_processes():
    return [
        "Mundra",
        "Gandhidham",
        "Party",
    ]


@router.get("/transportations")
def get_transportations():
    return [
        "Octopus",
        "Party",
        "Pending",
    ]


@router.get("/other-services")
def get_other_services():
    return [
        "Insurance",
        "CE Certificate",
        "Phyto",
        "Fumigation",
        "Lashing Chocking",
        "Palletisation",
    ]