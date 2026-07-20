from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
)

from backend.models.purchase_order import PurchaseOrderCreate
from backend.services.purchase_order_service import purchase_order_service


router = APIRouter(
    prefix="/purchase-orders",
    tags=["Purchase Orders"],
)


@router.get("")
def list_purchase_orders(
    search: str = "",
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
):
    return purchase_order_service.list(
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post("")
def create_purchase_order(
    purchase_order: PurchaseOrderCreate,
    background_tasks: BackgroundTasks,
):
    try:
        return purchase_order_service.create(
            data=purchase_order.model_dump(),
            background_tasks=background_tasks,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )