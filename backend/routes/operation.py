from fastapi import APIRouter, HTTPException, Query

from backend.models.operation import (
    PubOperationCreate,
    PubOperationUpdate,
    ImportOperationCreate,
    ImportOperationUpdate,
)
from backend.services.operation_service import (
    pub_operation_service,
    import_operation_service,
)


router = APIRouter()


# =========================================================
# PUB OPERATIONS
# =========================================================

@router.get(
    "/pub-operations",
    tags=["Pub Operations"],
)
def list_pub_operations(
    search: str = "",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
):
    return pub_operation_service.list(
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/pub-operations/{operation_id}",
    tags=["Pub Operations"],
)
def get_pub_operation(operation_id: str):
    return pub_operation_service.get(operation_id)


@router.post(
    "/pub-operations",
    tags=["Pub Operations"],
)
def create_pub_operation(
    operation: PubOperationCreate,
):
    try:
        return pub_operation_service.create(operation)

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.put(
    "/pub-operations/{operation_id}",
    tags=["Pub Operations"],
)
def update_pub_operation(
    operation_id: str,
    operation: PubOperationUpdate,
):
    try:
        return pub_operation_service.update(
            operation_id,
            operation,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.delete(
    "/pub-operations/{operation_id}",
    tags=["Pub Operations"],
)
def delete_pub_operation(operation_id: str):
    return pub_operation_service.delete(operation_id)


# =========================================================
# IMPORT OPERATIONS
# =========================================================

@router.get(
    "/import-operations",
    tags=["Import Operations"],
)
def list_import_operations(
    search: str = "",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
):
    return import_operation_service.list(
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/import-operations/{operation_id}",
    tags=["Import Operations"],
)
def get_import_operation(operation_id: str):
    return import_operation_service.get(operation_id)


@router.post(
    "/import-operations",
    tags=["Import Operations"],
)
def create_import_operation(
    operation: ImportOperationCreate,
):
    try:
        return import_operation_service.create(operation)

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.put(
    "/import-operations/{operation_id}",
    tags=["Import Operations"],
)
def update_import_operation(
    operation_id: str,
    operation: ImportOperationUpdate,
):
    try:
        return import_operation_service.update(
            operation_id,
            operation,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.delete(
    "/import-operations/{operation_id}",
    tags=["Import Operations"],
)
def delete_import_operation(operation_id: str):
    return import_operation_service.delete(operation_id)