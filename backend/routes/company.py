from fastapi import APIRouter, Depends

from backend.models.company import CompanyCreate
from backend.services.company_service import CompanyService
from backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.post("")
def create_company(
    company: CompanyCreate,
    user=Depends(get_current_user),
):
    return CompanyService.create(
        company,
        user["sub"],
    )


@router.get("")
def get_companies():
    return CompanyService.get_all()