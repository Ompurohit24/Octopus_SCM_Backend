from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
)

from backend.models.purchase_order import (
    PurchaseOrderCancel,
    PurchaseOrderCreate,
)
from backend.services.purchase_order_service import (
    purchase_order_service,
)


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


@router.get("/service-status")
def get_purchase_order_service_status(
    job_id: str = Query(...),
    category: str = Query(...),
    service_name: str = Query(...),
):
    """
    Check whether an Issued Purchase Order exists
    for a workflow service.

    Frontend calls this BEFORE allowing the user
    to uncheck/remove the service.
    """

    return purchase_order_service.get_issued_for_service(
        job_id=job_id,
        category=category,
        service_name=service_name,
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


@router.post("/cancel-service")
def cancel_purchase_order_service(
    cancellation: PurchaseOrderCancel,
    background_tasks: BackgroundTasks,
    job_id: str = Query(...),
    category: str = Query(...),
    service_name: str = Query(...),
):
    """
    Cancel an Issued Purchase Order after the user
    confirms removal/unchecking of its workflow service.

    The Purchase Order is NOT deleted.

    Status:
        Issued -> Cancelled

    Cancellation information is retained for audit/history.
    """

    try:
        return purchase_order_service.cancel_issued_service_po(
            job_id=job_id,
            category=category,
            service_name=service_name,
            reason=(
                cancellation.reason
                or "Service removed from Import Workflow"
            ),
            background_tasks=background_tasks,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )