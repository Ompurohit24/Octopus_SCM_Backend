import json

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from backend.models.customer import CustomerCreate, CustomerUpdate
from backend.services.customer_service import CustomerService
from backend.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


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
    # -------------------------------------------------
    # PARSE CUSTOMER EMAILS
    #
    # New frontend format:
    # '["one@example.com", "two@example.com"]'
    #
    # Backward-compatible old format:
    # "one@example.com"
    # -------------------------------------------------

    try:
        parsed_email = json.loads(email)

        if isinstance(parsed_email, list):
            emails = parsed_email

        elif isinstance(parsed_email, str):
            emails = [parsed_email]

        else:
            emails = [email]

    except (json.JSONDecodeError, TypeError):
        emails = [email]

    # Remove empty values and duplicate emails.
    cleaned_emails = []
    seen_emails = set()

    for item in emails:
        value = str(item).strip()

        if not value:
            continue

        normalized = value.lower()

        if normalized in seen_emails:
            continue

        seen_emails.add(normalized)
        cleaned_emails.append(value)

    if not cleaned_emails:
        raise HTTPException(
            status_code=422,
            detail="At least one email is required.",
        )

    # -------------------------------------------------
    # BUILD CUSTOMER MODEL
    # -------------------------------------------------

    customer = CustomerCreate(
        customer_name=customer_name,
        address=address,
        email=cleaned_emails,
        countryCode=countryCode,
        phone=phone,
        gstin=gstin,
        pan=pan,
        tan=tan,
    )

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
        "customer_code":
            CustomerService.get_next_customer_code()
    }


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


@router.put("/{customer_id}")
def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
):
    try:
        return CustomerService.update(
            customer_id,
            customer,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str,
):
    return CustomerService.delete(customer_id)