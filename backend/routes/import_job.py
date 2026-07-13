# from fastapi import APIRouter, Depends
from fastapi import APIRouter, Depends, HTTPException, status
from backend.models.import_job import ImportJobCreate, ImportJobUpdate
from backend.services.import_job_service import ImportJobService
from backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/import-jobs",
    tags=["Import Jobs"],
)


@router.post("")
def create_import_job(
    job: ImportJobCreate,
    user=Depends(get_current_user),
):
    try:
        return ImportJobService.create(
            job,
            user["sub"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

@router.get("/next-number")
def get_next_job_number():
    return {
        "job_number": ImportJobService.get_next_job_number()
    }


@router.get("")
def get_import_jobs(
    skip: int = 0,
    limit: int = 20,
    search: str = "",
):
    return ImportJobService.get_all(
        skip,
        limit,
        search,
    )


@router.get("/{job_id}")
def get_import_job(
    job_id: str,
):
    return ImportJobService.get_by_id(job_id)


@router.put("/{job_id}")
def update_import_job(
    job_id: str,
    job: ImportJobUpdate,
):
    return ImportJobService.update(
        job_id,
        job,
    )


@router.delete("/{job_id}")
def delete_import_job(
    job_id: str,
):
    return ImportJobService.delete(job_id)