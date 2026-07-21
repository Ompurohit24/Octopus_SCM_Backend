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
from backend.services.vendor_service import (
    vendor_service,
)
from pathlib import Path
import shutil

from pydantic import BaseModel

from backend.repositories.pending_registration_repository import (
    pending_registration_repository,
)
from backend.services.pending_registration_service import (
    pending_registration_service,
)
from backend.services.email_service import (
    email_service,
)
from backend.utils.dependencies import (
    get_current_user,
)
from fastapi import Depends

from backend.models.pending_registration import (
    ResendRegistrationOTPRequest,
)
router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)
class VendorOTPVerifyRequest(BaseModel):
    registration_id: str
    otp: str

# =========================================================
# NEXT VENDOR CODE
# =========================================================

@router.get("/next-code")
def get_next_vendor_code():
    return vendor_service.get_next_code()


# =========================================================
# LIST VENDORS
# =========================================================

@router.get("")
def list_vendors(
    search: str = "",
    skip: int = Query(
        0,
        ge=0,
    ),
    limit: int = Query(
        20,
        ge=1,
    ),
):
    return vendor_service.list(
        search=search,
        skip=skip,
        limit=limit,
    )

@router.post("/registration/start")
async def start_vendor_registration(
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

    user=Depends(get_current_user),
):
    email = email.strip()

    if not email:
        raise HTTPException(
            status_code=422,
            detail="Vendor email is required.",
        )

    # Validate all Vendor fields without creating Vendor.
    vendor = VendorCreate(
        vendor_code="",
        vendor_name=vendor_name,
        address=address,
        email=email,
        countryCode=countryCode,
        phone=phone,
        gstin=gstin,
        pan=pan,
        type_of_service=type_of_service,
    )

    form_data = vendor.model_dump(
        mode="json"
    )

    # Final code generated only after OTP verification.
    form_data.pop(
        "vendor_code",
        None,
    )

    temporary_documents = {}

    try:
        registration_result = (
            pending_registration_service
            .start_vendor_registration(
                form_data=form_data,
                created_by=user["sub"],
                temporary_documents={},
            )
        )

        registration = registration_result[
            "registration"
        ]

        registration_id = str(
            registration[
                "registration_id"
            ]
        )

        otp = registration_result[
            "plain_otps"
        ][
            "vendor_email"
        ]

        # ---------------------------------------------
        # SAVE TEMPORARY KYC
        # ---------------------------------------------

        pending_root = (
            Path("KYC")
            / "Pending"
            / "Vendor"
            / registration_id
        )

        pending_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        if gst_document:
            extension = Path(
                gst_document.filename
            ).suffix

            gst_path = (
                pending_root
                / f"GST{extension}"
            )

            with open(
                gst_path,
                "wb",
            ) as buffer:
                shutil.copyfileobj(
                    gst_document.file,
                    buffer,
                )

            temporary_documents[
                "gst_document"
            ] = str(gst_path)

        if pan_document:
            extension = Path(
                pan_document.filename
            ).suffix

            pan_path = (
                pending_root
                / f"PAN{extension}"
            )

            with open(
                pan_path,
                "wb",
            ) as buffer:
                shutil.copyfileobj(
                    pan_document.file,
                    buffer,
                )

            temporary_documents[
                "pan_document"
            ] = str(pan_path)

        if temporary_documents:
            pending_registration_repository \
                .update_registration(
                    registration_id=
                        registration_id,

                    update_data={
                        "temporary_documents":
                            temporary_documents,
                    },
                )

        # ---------------------------------------------
        # SEND SINGLE VENDOR OTP
        # ---------------------------------------------

        sent = (
            email_service
            .send_registration_otp_email(
                recipient_email=email,
                otp=otp,
                entity_type="vendor",
                entity_name=vendor_name,
                email_role="Vendor Email",
            )
        )

        return {
            "registration_id":
                registration_id,

            "entity_type":
                "vendor",

            "entity_name":
                vendor_name,

            "status":
                "pending",

            "expires_at":
                registration[
                    "expires_at"
                ],

            "verification_fields": [
                {
                    "key":
                        "vendor_email",

                    "label":
                        "Vendor Email",

                    "email":
                        email,

                    "otp_sent":
                        sent,
                }
            ],

            "all_otps_sent":
                sent,

            "message":
                (
                    "OTP sent successfully. "
                    "Verify the Vendor email "
                    "to create the Vendor profile."
                    if sent
                    else
                    "Vendor verification was started, "
                    "but the OTP email could not be sent. "
                    "Please resend the pending OTP."
                ),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
# =========================================================
# GET VENDOR
# =========================================================



@router.post("/registration/verify")
def verify_vendor_registration(
    data: VendorOTPVerifyRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    try:
        registration = (
            pending_registration_repository
            .find_by_registration_id(
                data.registration_id
            )
        )

        if not registration:
            raise ValueError(
                "Pending Vendor registration "
                "not found."
            )

        if (
            registration.get(
                "entity_type"
            )
            != "vendor"
        ):
            raise ValueError(
                "Invalid Vendor registration."
            )

        if (
            registration.get(
                "created_by"
            )
            != user["sub"]
        ):
            raise ValueError(
                "You are not authorized to verify "
                "this Vendor registration."
            )

        if (
            registration.get(
                "status"
            )
            != "pending"
        ):
            raise ValueError(
                "Vendor registration is no longer "
                "pending."
            )

        # ---------------------------------------------
        # VERIFY SINGLE VENDOR OTP
        # ---------------------------------------------

        result = (
            pending_registration_service
            .verify_email_otp(
                registration_id=
                    data.registration_id,

                email_key=
                    "vendor_email",

                otp=
                    data.otp,
            )
        )

        if not result.get(
            "verified"
        ):
            raise ValueError(
                "OTP verification failed."
            )

        # ---------------------------------------------
        # RELOAD REGISTRATION
        # ---------------------------------------------

        registration = (
            pending_registration_repository
            .find_by_registration_id(
                data.registration_id
            )
        )

        verification = (
            registration.get(
                "email_verifications",
                {},
            )
            .get(
                "vendor_email"
            )
        )

        if not verification:
            raise ValueError(
                "Vendor email verification "
                "not found."
            )

        if not verification.get(
            "verified",
            False,
        ):
            return {
                "created":
                    False,

                "all_verified":
                    False,

                "message":
                    "Vendor email is still "
                    "awaiting verification.",
            }

        # ---------------------------------------------
        # FINAL VENDOR CREATION
        # ---------------------------------------------

        vendor = (
            vendor_service
            .create_from_verified_registration(
                registration=
                    registration,

                user_id=
                    user["sub"],

                background_tasks=
                    background_tasks,
            )
        )

        return {
            "created":
                True,

            "all_verified":
                True,

            "vendor":
                vendor,

            "message":
                (
                    "Vendor verified and "
                    "created successfully."
                ),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get(
    "/registration/pending/{registration_id}"
)
def get_pending_vendor_registration(
    registration_id: str,
    user=Depends(get_current_user),
):
    try:
        result = (
            pending_registration_service
            .get_pending_registration(
                registration_id=
                    registration_id,

                user_id=
                    user["sub"],
            )
        )

        if (
            result.get(
                "entity_type"
            )
            != "vendor"
        ):
            raise ValueError(
                "Invalid Vendor registration."
            )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )



@router.post(
    "/registration/resend-otp"
)
def resend_vendor_registration_otp(
    data: ResendRegistrationOTPRequest,
    user=Depends(get_current_user),
):
    if (
        data.email_key
        != "vendor_email"
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Vendor email field.",
        )

    try:
        result = (
            pending_registration_service
            .resend_otp(
                registration_id=
                    data.registration_id,

                email_key=
                    "vendor_email",

                user_id=
                    user["sub"],
            )
        )

        registration = (
            result[
                "registration"
            ]
        )

        if (
            registration.get(
                "entity_type"
            )
            != "vendor"
        ):
            raise ValueError(
                "Invalid Vendor registration."
            )

        sent = (
            email_service
            .send_registration_otp_email(
                recipient_email=
                    result[
                        "email"
                    ],

                otp=
                    result[
                        "otp"
                    ],

                entity_type=
                    "vendor",

                entity_name=
                    registration.get(
                        "entity_name",
                        "",
                    ),

                email_role=
                    "Vendor Email",
            )
        )

        return {
            "sent":
                sent,

            "email_key":
                "vendor_email",

            "email":
                result[
                    "email"
                ],

            "otp_expires_at":
                result[
                    "otp_expires_at"
                ],

            "message":
                (
                    "New OTP sent successfully."
                    if sent
                    else
                    "Unable to send OTP email."
                ),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: str,
):
    return vendor_service.get(
        vendor_id
    )


# =========================================================
# CREATE VENDOR
# =========================================================

@router.post("")
async def create_vendor(
    background_tasks: BackgroundTasks,

    vendor_code: str = Form(""),
    vendor_name: str = Form(...),
    address: str = Form(...),

    # Vendor has exactly ONE email.
    email: str = Form(...),

    countryCode: str = Form("+91"),
    phone: str = Form(...),

    gstin: str = Form(...),
    pan: str = Form(...),

    type_of_service: str = Form(...),

    gst_document: UploadFile | None = File(
        None
    ),

    pan_document: UploadFile | None = File(
        None
    ),
):
    # -------------------------------------------------
    # CLEAN SINGLE VENDOR EMAIL
    # -------------------------------------------------

    email = email.strip()

    if not email:
        raise HTTPException(
            status_code=422,
            detail="Vendor email is required.",
        )

    # -------------------------------------------------
    # BUILD VENDOR MODEL
    #
    # Pydantic EmailStr validates email format.
    # -------------------------------------------------

    vendor = VendorCreate(
        vendor_code=vendor_code,
        vendor_name=vendor_name,
        address=address,
        email=email,
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


# =========================================================
# UPDATE VENDOR
# =========================================================

@router.put("/{vendor_id}")
async def update_vendor(
    vendor_id: str,

    vendor_code: str | None = Form(
        None
    ),

    vendor_name: str | None = Form(
        None
    ),

    address: str | None = Form(
        None
    ),

    # Vendor has exactly ONE email.
    email: str | None = Form(
        None
    ),

    countryCode: str | None = Form(
        None
    ),

    phone: str | None = Form(
        None
    ),

    gstin: str | None = Form(
        None
    ),

    pan: str | None = Form(
        None
    ),

    type_of_service: str | None = Form(
        None
    ),

    gst_document: UploadFile | None = File(
        None
    ),

    pan_document: UploadFile | None = File(
        None
    ),
):
    # -------------------------------------------------
    # BUILD PARTIAL UPDATE
    # -------------------------------------------------

    update_data = {}

    if vendor_code is not None:
        update_data[
            "vendor_code"
        ] = vendor_code

    if vendor_name is not None:
        update_data[
            "vendor_name"
        ] = vendor_name

    if address is not None:
        update_data[
            "address"
        ] = address

    # -------------------------------------------------
    # SINGLE EMAIL
    # -------------------------------------------------

    if email is not None:

        cleaned_email = (
            email.strip()
        )

        if not cleaned_email:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Vendor email "
                    "cannot be empty."
                ),
            )

        update_data[
            "email"
        ] = cleaned_email

    if countryCode is not None:
        update_data[
            "countryCode"
        ] = countryCode

    if phone is not None:
        update_data[
            "phone"
        ] = phone

    if gstin is not None:
        update_data[
            "gstin"
        ] = gstin

    if pan is not None:
        update_data[
            "pan"
        ] = pan

    if type_of_service is not None:
        update_data[
            "type_of_service"
        ] = type_of_service

    # -------------------------------------------------
    # VALIDATE UPDATE MODEL
    # -------------------------------------------------

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


# =========================================================
# DELETE VENDOR
# =========================================================

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