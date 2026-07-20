from fastapi import APIRouter, Depends
from fastapi import APIRouter, Depends, HTTPException
from backend.models.import_workflow import (
    ImportWorkflowCreate,
    ImportWorkflowUpdate,
)
from backend.services.import_workflow_service import ImportWorkflowService
from backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/import-workflows",
    tags=["Import Workflows"],
)


@router.get("")
def search_import_workflows(
    search: str = "",
    skip: int = 0,
    limit: int = 20,
):
    return ImportWorkflowService.search(
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post("/{job_id}")
def create_import_workflow(
    job_id: str,
    workflow: ImportWorkflowCreate,
    user=Depends(get_current_user),
):
    return ImportWorkflowService.create(
        job_id=job_id,
        workflow=workflow,
        user_id=user["sub"],
    )


@router.get("/{job_id}")
def get_import_workflow(
    job_id: str,
):
    return ImportWorkflowService.get(job_id)


@router.put("/{job_id}")
def update_import_workflow(
    job_id: str,
    workflow: ImportWorkflowUpdate,
    user=Depends(get_current_user),
):
    try:
        return ImportWorkflowService.update(
            job_id=job_id,
            workflow=workflow,
            user_id=user["sub"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )


@router.delete("/{job_id}")
def delete_import_workflow(
    job_id: str,
):
    return ImportWorkflowService.delete(job_id)

@router.get("/search/jobs")
def search_jobs(
    search: str = "",
    skip: int = 0,
    limit: int = 20,
):
    return ImportWorkflowService.search_jobs(
        search=search,
        skip=skip,
        limit=limit,
    )