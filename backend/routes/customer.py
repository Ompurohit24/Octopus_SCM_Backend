# from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
)
from backend.models.customer import CustomerCreate, CustomerUpdate
from backend.services.customer_service import CustomerService
from backend.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)

@router.post("")
@router.post("")
async def create_customer(


    background_tasks: BackgroundTasks,

    customer_name: str = Form(...),
    address: str = Form(...),
    email: str = Form(...),

    countryCode: str = Form("+91"),
    phone: str = Form(...),

    gstin: str = Form(...),
    pan: str = Form(...),
    tan: str = Form(""),

    gst_document: UploadFile | None = File(None),
    pan_document: UploadFile | None = File(None),

    user=Depends(get_current_user),
):
    customer = CustomerCreate(
        customer_name=customer_name,
        address=address,
        email=email,
        countryCode=countryCode,
        phone=phone,
        gstin=gstin,
        pan=pan,
        tan=tan,
    )

    from fastapi import HTTPException
    
    try:
        return CustomerService.create(
            customer=customer,
            user_id=user["sub"],
            background_tasks=background_tasks,
            gst_document=gst_document,
            pan_document=pan_document,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),


        )
@router.get("/next-code")
def get_next_customer_code():
    return {
        "customer_code": CustomerService.get_next_customer_code()
    }

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