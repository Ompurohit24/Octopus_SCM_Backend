from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from backend.models.import_job import ImportJobCreate, ImportJobUpdate
from backend.services.import_job_service import ImportJobService
from backend.services.import_pdf_service import import_pdf_service
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

@router.post("/read-pdf")
async def read_import_job_pdf(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="PDF file is required.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty.",
        )

    # 15 MB protection
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="PDF file is too large. Maximum size is 15 MB.",
        )

    try:
        extracted = import_pdf_service.extract_import_job(
            content
        )

        return {
            "success": True,
            "filename": file.filename,
            "data": extracted,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to read Import Job PDF.",
        ) from exc