from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from backend.models.pending_registration import (
    ResendRegistrationOTPRequest,
)
from pydantic import BaseModel
from pathlib import Path
import shutil

from backend.repositories.pending_registration_repository import (
    pending_registration_repository,
)
from backend.services.pending_registration_service import (
    pending_registration_service,
)

from backend.services.email_service import (
    email_service,
)
from backend.models.customer import (
    CustomerCreate,
    CustomerUpdate,
)
from backend.services.customer_service import (
    CustomerService,
)
from backend.utils.dependencies import (
    get_current_user,
)

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


class CustomerOTPVerifyRequest(BaseModel):
    registration_id: str

    management_email_otp: str | None = None
    accounts_email_otp: str | None = None
    operations_email_otp: str | None = None


# =========================================================
# CREATE CUSTOMER
# =========================================================


@router.post("/registration/start")
async def start_customer_registration(
        customer_name: str = Form(...),
        address: str = Form(...),

        management_email: str | None = Form(None),
        accounts_email: str | None = Form(None),
        operations_email: str | None = Form(None),

        countryCode: str = Form("+91"),
        phone: str = Form(...),

        gstin: str = Form(...),
        pan: str = Form(...),
        tan: str = Form(""),

        gst_document: UploadFile | None = File(None),
        pan_document: UploadFile | None = File(None),

        user=Depends(
            get_current_user
        ),
):
    # -------------------------------------------------
    # CLEAN EMAILS
    # -------------------------------------------------

    management_email = (
        management_email.strip()
        if management_email
        else None
    )

    accounts_email = (
        accounts_email.strip()
        if accounts_email
        else None
    )

    operations_email = (
        operations_email.strip()
        if operations_email
        else None
    )

    if not any(
            [
                management_email,
                accounts_email,
                operations_email,
            ]
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "At least one Customer "
                "email is required."
            ),
        )

    # -------------------------------------------------
    # VALIDATE CUSTOMER DATA
    #
    # This validates EmailStr and all Customer fields,
    # but DOES NOT create the Customer.
    # -------------------------------------------------

    customer = CustomerCreate(
        customer_name=customer_name,
        address=address,

        management_email=
        management_email,

        accounts_email=
        accounts_email,

        operations_email=
        operations_email,

        countryCode=countryCode,
        phone=phone,

        gstin=gstin,
        pan=pan,
        tan=tan,
    )

    # -------------------------------------------------
    # BUILD TEMPORARY FORM DATA
    # -------------------------------------------------

    form_data = (
        customer.model_dump(
            mode="json"
        )
    )

    # Customer code must be generated only when the
    # final Customer is actually created.
    form_data.pop(
        "customer_code",
        None,
    )

    # -------------------------------------------------
    # TEMPORARY KYC DOCUMENTS
    #
    # For now we store the uploaded documents in a
    # pending folder so they survive closing/reloading
    # the OTP dialog.
    # -------------------------------------------------

    temporary_documents = {}

    registration_result = None

    try:
        # ---------------------------------------------
        # FIRST CREATE PENDING REGISTRATION
        #
        # We need registration_id before creating its
        # permanent temporary-document folder.
        # ---------------------------------------------

        registration_result = (
            pending_registration_service
            .start_customer_registration(
                form_data=form_data,

                created_by=user[
                    "sub"
                ],

                temporary_documents={},
            )
        )

        registration = (
            registration_result[
                "registration"
            ]
        )

        registration_id = str(
            registration[
                "registration_id"
            ]
        )

        plain_otps = (
            registration_result[
                "plain_otps"
            ]
        )

        # ---------------------------------------------
        # SAVE TEMPORARY KYC FILES
        # ---------------------------------------------

        pending_root = (
                Path("KYC")
                / "Pending"
                / "Customer"
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
            ] = str(
                gst_path
            )

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
            ] = str(
                pan_path
            )

        # ---------------------------------------------
        # SAVE TEMP DOCUMENT PATHS
        # ---------------------------------------------

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
        # SEND OTP TO EVERY ENTERED CUSTOMER EMAIL
        # ---------------------------------------------

        email_roles = {
            "management_email":
                "Management Email",

            "accounts_email":
                "Accounts Email",

            "operations_email":
                "Operations Email",
        }

        verification_fields = []

        for (
                email_key,
                otp,
        ) in plain_otps.items():

            email_address = (
                form_data.get(
                    email_key
                )
            )

            if not email_address:
                continue

            sent = (
                email_service
                .send_registration_otp_email(
                    recipient_email=
                    email_address,

                    otp=
                    otp,

                    entity_type=
                    "customer",

                    entity_name=
                    customer_name,

                    email_role=
                    email_roles[
                        email_key
                    ],
                )
            )

            verification_fields.append(
                {
                    "key":
                        email_key,

                    "label":
                        email_roles[
                            email_key
                        ],

                    "email":
                        email_address,

                    "otp_sent":
                        sent,
                }
            )

        failed_fields = [
            field
            for field
            in verification_fields
            if not field[
                "otp_sent"
            ]
        ]

        all_otps_sent = (
                len(
                    failed_fields
                )
                == 0
        )
        # ---------------------------------------------
        # RETURN ONLY SAFE DATA
        #
        # NEVER return OTP or OTP hash.
        # ---------------------------------------------

        return {
            "registration_id":
                registration_id,

            "entity_type":
                "customer",

            "entity_name":
                customer_name,

            "status":
                "pending",

            "expires_at":
                registration[
                    "expires_at"
                ],

            "verification_fields":
                verification_fields,

            "all_otps_sent":
                all_otps_sent,

            "message":
                (
                    "OTP sent successfully. "
                    "Verify all entered email "
                    "addresses to create the "
                    "Customer profile."
                    if all_otps_sent
                    else
                    "Customer verification was "
                    "started, but one or more OTP "
                    "emails could not be sent. "
                    "Please resend the pending OTP."
                ),
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# @router.post("")
# async def create_customer(
#     background_tasks: BackgroundTasks,
#
#     customer_name: str = Form(...),
#     address: str = Form(...),
#
#     # -------------------------------------------------
#     # FIXED CUSTOMER EMAIL FIELDS
#     #
#     # Customer can enter 1, 2, or all 3.
#     # At least one is required.
#     # -------------------------------------------------
#
#     management_email: str | None = Form(
#         None
#     ),
#
#     accounts_email: str | None = Form(
#         None
#     ),
#
#     operations_email: str | None = Form(
#         None
#     ),
#
#     countryCode: str = Form("+91"),
#
#     phone: str = Form(...),
#
#     gstin: str = Form(...),
#
#     pan: str = Form(...),
#
#     tan: str = Form(""),
#
#     gst_document: UploadFile | None = File(
#         None
#     ),
#
#     pan_document: UploadFile | None = File(
#         None
#     ),
#
#     user=Depends(
#         get_current_user
#     ),
# ):
#     # -------------------------------------------------
#     # CLEAN EMAIL VALUES
#     # -------------------------------------------------
#
#     management_email = (
#         management_email.strip()
#         if management_email
#         else None
#     )
#
#     accounts_email = (
#         accounts_email.strip()
#         if accounts_email
#         else None
#     )
#
#     operations_email = (
#         operations_email.strip()
#         if operations_email
#         else None
#     )
#
#     # -------------------------------------------------
#     # AT LEAST ONE EMAIL REQUIRED
#     # -------------------------------------------------
#
#     if not any(
#         [
#             management_email,
#             accounts_email,
#             operations_email,
#         ]
#     ):
#         raise HTTPException(
#             status_code=422,
#             detail=(
#                 "At least one Customer "
#                 "email is required."
#             ),
#         )
#
#     # -------------------------------------------------
#     # BUILD CUSTOMER MODEL
#     #
#     # EmailStr in CustomerCreate validates every
#     # entered email independently.
#     # -------------------------------------------------
#
#     customer = CustomerCreate(
#         customer_name=customer_name,
#         address=address,
#
#         management_email=
#             management_email,
#
#         accounts_email=
#             accounts_email,
#
#         operations_email=
#             operations_email,
#
#         countryCode=countryCode,
#
#         phone=phone,
#
#         gstin=gstin,
#
#         pan=pan,
#
#         tan=tan,
#     )
#
#     try:
#         return CustomerService.create(
#             customer=customer,
#
#             user_id=user[
#                 "sub"
#             ],
#
#             background_tasks=
#                 background_tasks,
#
#             gst_document=
#                 gst_document,
#
#             pan_document=
#                 pan_document,
#         )
#
#     except ValueError as e:
#         raise HTTPException(
#             status_code=409,
#             detail=str(e),
#         )


# =========================================================
# NEXT CUSTOMER CODE
# =========================================================

@router.get("/next-code")
def get_next_customer_code():
    return {
        "customer_code":
            CustomerService
            .get_next_customer_code()
    }


# =========================================================
# LIST CUSTOMERS
# =========================================================


@router.post("/registration/verify")
def verify_customer_registration(
        data: CustomerOTPVerifyRequest,
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
                "Pending Customer registration not found."
            )

        if (
                registration.get("entity_type")
                != "customer"
        ):
            raise ValueError(
                "Invalid Customer registration."
            )

        if (
                registration.get("created_by")
                != user["sub"]
        ):
            raise ValueError(
                "You are not authorized to verify "
                "this Customer registration."
            )

        if (
                registration.get("status")
                != "pending"
        ):
            raise ValueError(
                "Customer registration is no longer pending."
            )

        # -------------------------------------------------
        # VERIFY ONLY THE EMAIL OTP SUBMITTED
        #
        # Frontend now verifies each Customer email
        # independently.
        # -------------------------------------------------

        otp_values = {
            "management_email":
                data.management_email_otp,

            "accounts_email":
                data.accounts_email_otp,

            "operations_email":
                data.operations_email_otp,
        }

        submitted_otps = {
            email_key: otp
            for email_key, otp
            in otp_values.items()
            if otp and otp.strip()
        }

        if not submitted_otps:
            raise ValueError(
                "OTP is required."
            )

        # One Verify button = one email verification.
        if len(submitted_otps) != 1:
            raise ValueError(
                "Verify one email at a time."
            )

        email_key, otp = next(
            iter(
                submitted_otps.items()
            )
        )

        verifications = (
            registration.get(
                "email_verifications",
                {},
            )
        )

        verification = (
            verifications.get(
                email_key
            )
        )

        if not verification:
            raise ValueError(
                "Email verification not found."
            )

        result = (
            pending_registration_service
            .verify_email_otp(
                registration_id=
                data.registration_id,

                email_key=
                email_key,

                otp=
                otp,
            )
        )

        if not result.get(
                "verified"
        ):
            raise ValueError(
                "OTP verification failed."
            )

        # -------------------------------------------------
        # RELOAD AFTER OTP VERIFICATION
        # -------------------------------------------------

        registration = (
            pending_registration_repository
            .find_by_registration_id(
                data.registration_id
            )
        )

        verifications = (
            registration.get(
                "email_verifications",
                {},
            )
        )

        all_verified = (
                bool(verifications)
                and all(
            item.get(
                "verified",
                False,
            )
            for item
            in verifications.values()
        )
        )

        if not all_verified:
            return {
                "created": False,
                "all_verified": False,
                "message":
                    "Some email addresses are "
                    "still awaiting verification.",
            }

        # -------------------------------------------------
        # FINAL CUSTOMER CREATION
        # -------------------------------------------------

        customer = (
            CustomerService
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
            "created": True,

            "all_verified": True,

            "customer":
                customer,

            "message":
                "Customer verified and created successfully.",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


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


# =========================================================
# UPDATE CUSTOMER
# =========================================================

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


# =========================================================
# DELETE CUSTOMER
# =========================================================

@router.delete("/{customer_id}")
def delete_customer(
        customer_id: str,
):
    try:
        return CustomerService.delete(
            customer_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=
            status.HTTP_409_CONFLICT,

            detail=str(e),
        )


@router.get(
    "/registration/pending/{registration_id}"
)
def get_pending_customer_registration(
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
                != "customer"
        ):
            raise ValueError(
                "Invalid Customer registration."
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
def resend_customer_registration_otp(
        data: ResendRegistrationOTPRequest,
        user=Depends(get_current_user),
):
    allowed_keys = {
        "management_email",
        "accounts_email",
        "operations_email",
    }

    if (
            data.email_key
            not in allowed_keys
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid Customer "
                "email field."
            ),
        )

    try:
        result = (
            pending_registration_service
            .resend_otp(
                registration_id=
                data.registration_id,

                email_key=
                data.email_key,

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
                != "customer"
        ):
            raise ValueError(
                "Invalid Customer registration."
            )

        labels = {
            "management_email":
                "Management Email",

            "accounts_email":
                "Accounts Email",

            "operations_email":
                "Operations Email",
        }

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
                "customer",

                entity_name=(
                        registration.get(
                            "entity_name"
                        )
                        or registration.get(
                    "form_data",
                    {},
                ).get(
                    "customer_name"
                )
                        or "Customer"
                ),

                email_role=
                labels[
                    data.email_key
                ],
            )
        )

        return {
            "sent":
                sent,

            "email_key":
                data.email_key,

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