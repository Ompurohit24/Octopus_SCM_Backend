from fastapi import APIRouter

from backend.services.import_workflow_history_service import (
    import_workflow_history_service,
)

router = APIRouter(
    prefix="/import-workflow-history",
    tags=["Import Workflow History"],
)


@router.get("/{workflow_id}")
def get_workflow_history(
    workflow_id: str,
):
    return import_workflow_history_service.get_history(
        workflow_id,
    )