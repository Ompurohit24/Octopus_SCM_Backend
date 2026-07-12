from fastapi import APIRouter

from backend.services.dropdown_service import dropdown_service

router = APIRouter(
    prefix="/dropdowns",
    tags=["Dropdowns"],
)


@router.get("/import-workflow")
def get_import_workflow_dropdowns():
    return dropdown_service.get_import_workflow_dropdowns()