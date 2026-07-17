from fastapi import APIRouter, HTTPException, Query

from backend.services.type_of_service_service import type_of_service_service

router = APIRouter(prefix="/masters/type-of-services", tags=["Type Of Services"])


@router.get("")
def get_all(search: str | None = None):
    return type_of_service_service.get_all(search)


@router.post("")
def create(name: str = Query(...)):
    try:
        return type_of_service_service.create(name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{old_name}")
def update(old_name: str, new_name: str = Query(...)):
    try:
        return type_of_service_service.update(old_name, new_name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{name}")
def delete(name: str):
    try:
        type_of_service_service.delete(name)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))