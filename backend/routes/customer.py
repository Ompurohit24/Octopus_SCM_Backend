# from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import APIRouter, Depends, BackgroundTasks
from backend.models.customer import CustomerCreate, CustomerUpdate
from backend.services.customer_service import CustomerService
from backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


# @router.post("")
# def create_customer(
#     customer: CustomerCreate,
#     user=Depends(get_current_user),
# ):
#     return CustomerService.create(
#         customer,
#         user["sub"],
#     )
@router.post("")
def create_customer(
    customer: CustomerCreate,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    return CustomerService.create(
        customer,
        user["sub"],
        background_tasks,
    )

@router.get("")
def get_customers(
    skip: int = 0,
    limit: int = 20,
):
    return CustomerService.get_all(skip, limit)


@router.put("/{customer_id}")
def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
):
    return CustomerService.update(
        customer_id,
        customer,
    )


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str,
):
    return CustomerService.delete(customer_id)

@router.get("")
def get_customers(
    skip: int = 0,
    limit: int = 20,
    search: str = "",
):
    return CustomerService.get_all(
        skip,
        limit,
        search,
    )