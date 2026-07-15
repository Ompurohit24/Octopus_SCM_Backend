from fastapi import APIRouter
from fastapi import APIRouter, HTTPException
from backend.services.dropdown_service import dropdown_service

router = APIRouter(
    prefix="/masters",
    tags=["Masters"],
)

from backend.services.line_name_service import (
    line_name_service,
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

@router.post("/line-names")
def create_line_name(name: str):
    try:
        return line_name_service.create(name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/line-names")
def create_line_name(
    name: str,
):
    return line_name_service.create(name)


@router.delete("/line-names/{name}")
def delete_line_name(
    name: str,
):
    return line_name_service.delete(name)

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