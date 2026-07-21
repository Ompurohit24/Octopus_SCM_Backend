import json

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from backend.models.vendor import (
    VendorCreate,
    VendorUpdate,
)
from backend.services.vendor_service import vendor_service


router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)


@router.get("/next-code")
def get_next_vendor_code():
    return vendor_service.get_next_code()


@router.get("")
def list_vendors(
    search: str = "",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1),
):
    return vendor_service.list(
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: str,
):
    return vendor_service.get(
        vendor_id
    )


@router.post("")
async def create_vendor(
    background_tasks: BackgroundTasks,

    vendor_code: str = Form(""),
    vendor_name: str = Form(...),
    address: str = Form(...),

    email: str = Form(...),

    countryCode: str = Form("+91"),
    phone: str = Form(...),

    gstin: str = Form(...),
    pan: str = Form(...),

    type_of_service: str = Form(...),

    gst_document: UploadFile | None = File(None),
    pan_document: UploadFile | None = File(None),
):
    # -----------------------------------------
    # PARSE MULTIPLE EMAILS
    #
    # Frontend may send:
    # ["one@example.com", "two@example.com"]
    #
    # Also supports old single-email format.
    # -----------------------------------------

    try:
        parsed_email = json.loads(email)

        if isinstance(parsed_email, list):
            emails = parsed_email

        elif isinstance(parsed_email, str):
            emails = [parsed_email]

        else:
            emails = [email]

    except (
        json.JSONDecodeError,
        TypeError,
    ):
        emails = [email]

    # -----------------------------------------
    # CLEAN EMAILS
    # -----------------------------------------

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
            detail=(
                "At least one email is required."
            ),
        )

    # -----------------------------------------
    # BUILD VENDOR MODEL
    # -----------------------------------------

    vendor = VendorCreate(
        vendor_code=vendor_code,
        vendor_name=vendor_name,
        address=address,
        email=cleaned_emails,
        countryCode=countryCode,
        phone=phone,
        gstin=gstin,
        pan=pan,
        type_of_service=type_of_service,
    )

    try:
        return vendor_service.create(
            vendor=vendor,
            background_tasks=background_tasks,
            gst_document=gst_document,
            pan_document=pan_document,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.put("/{vendor_id}")
async def update_vendor(
    vendor_id: str,

    vendor_code: str | None = Form(None),
    vendor_name: str | None = Form(None),
    address: str | None = Form(None),

    email: str | None = Form(None),

    countryCode: str | None = Form(None),
    phone: str | None = Form(None),

    gstin: str | None = Form(None),
    pan: str | None = Form(None),

    type_of_service: str | None = Form(None),

    gst_document: UploadFile | None = File(None),
    pan_document: UploadFile | None = File(None),
):
    # -----------------------------------------
    # PARSE EMAILS
    # -----------------------------------------

    cleaned_emails = None

    if email is not None:
        try:
            parsed_email = json.loads(email)

            if isinstance(parsed_email, list):
                emails = parsed_email
            elif isinstance(parsed_email, str):
                emails = [parsed_email]
            else:
                emails = []

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            emails = [email]

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

    # -----------------------------------------
    # BUILD UPDATE MODEL
    # -----------------------------------------

    update_data = {}

    if vendor_code is not None:
        update_data["vendor_code"] = vendor_code

    if vendor_name is not None:
        update_data["vendor_name"] = vendor_name

    if address is not None:
        update_data["address"] = address

    if cleaned_emails is not None:
        update_data["email"] = cleaned_emails

    if countryCode is not None:
        update_data["countryCode"] = countryCode

    if phone is not None:
        update_data["phone"] = phone

    if gstin is not None:
        update_data["gstin"] = gstin

    if pan is not None:
        update_data["pan"] = pan

    if type_of_service is not None:
        update_data["type_of_service"] = (
            type_of_service
        )

    vendor = VendorUpdate(
        **update_data
    )

    try:
        return vendor_service.update(
            vendor_id=vendor_id,
            vendor=vendor,
            gst_document=gst_document,
            pan_document=pan_document,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: str,
):
    try:
        return vendor_service.delete(
            vendor_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=str(e),
        )