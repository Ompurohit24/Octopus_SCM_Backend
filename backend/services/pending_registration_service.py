import hashlib
import hmac
import secrets
import uuid

from datetime import datetime, timedelta, timezone

from backend.config.settings import settings
from backend.repositories.pending_registration_repository import (
    pending_registration_repository,
)


class PendingRegistrationService:

    OTP_VALID_HOURS = 24

    # =====================================================
    # OTP GENERATION
    # =====================================================

    @staticmethod
    def generate_otp() -> str:
        """
        Generate a cryptographically secure
        6-digit OTP.
        """

        return f"{secrets.randbelow(1000000):06d}"

    # =====================================================
    # OTP HASH
    #
    # Never store the actual OTP in MongoDB.
    # =====================================================

    @staticmethod
    def hash_otp(
        registration_id: str,
        email_key: str,
        otp: str,
    ) -> str:

        value = (
            f"{registration_id}:"
            f"{email_key}:"
            f"{otp}"
        )

        return hmac.new(
            key=settings.JWT_SECRET_KEY.encode(
                "utf-8"
            ),
            msg=value.encode(
                "utf-8"
            ),
            digestmod=hashlib.sha256,
        ).hexdigest()

    # =====================================================
    # OTP CHECK
    # =====================================================

    @classmethod
    def verify_otp_hash(
        cls,
        registration_id: str,
        email_key: str,
        otp: str,
        stored_hash: str,
    ) -> bool:

        calculated_hash = cls.hash_otp(
            registration_id=
                registration_id,

            email_key=
                email_key,

            otp=
                otp,
        )

        return hmac.compare_digest(
            calculated_hash,
            stored_hash,
        )

    # =====================================================
    # BUILD EMAIL VERIFICATION
    # =====================================================

    @classmethod
    def build_email_verification(
        cls,
        registration_id: str,
        email_key: str,
        email: str,
    ) -> tuple[dict, str]:

        otp = cls.generate_otp()

        verification = {
            "email":
                email,

            "otp_hash":
                cls.hash_otp(
                    registration_id=
                        registration_id,

                    email_key=
                        email_key,

                    otp=
                        otp,
                ),

            "verified":
                False,

            "verified_at":
                None,
        }

        return (
            verification,
            otp,
        )

    # =====================================================
    # START CUSTOMER REGISTRATION
    # =====================================================

    @classmethod
    def start_customer_registration(
        cls,
        form_data: dict,
        created_by: str,
        temporary_documents: dict | None = None,
    ) -> dict:

        registration_id = str(
            uuid.uuid4()
        )

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            now
            + timedelta(
                hours=
                    cls.OTP_VALID_HOURS
            )
        )

        email_verifications = {}

        plain_otps = {}

        customer_email_fields = [
            "management_email",
            "accounts_email",
            "operations_email",
        ]

        for email_key in (
            customer_email_fields
        ):

            email = form_data.get(
                email_key
            )

            if not email:
                continue

            email = str(
                email
            ).strip()

            if not email:
                continue

            (
                verification,
                otp,
            ) = (
                cls
                .build_email_verification(
                    registration_id=
                        registration_id,

                    email_key=
                        email_key,

                    email=
                        email,
                )
            )

            email_verifications[
                email_key
            ] = verification

            plain_otps[
                email_key
            ] = otp

        if not email_verifications:
            raise ValueError(
                "At least one Customer "
                "email is required."
            )

        document = {
            "registration_id":
                registration_id,

            "entity_type":
                "customer",

            "entity_name":
                str(
                    form_data.get(
                        "customer_name",
                        "",
                    )
                    or ""
                ).strip(),

            "form_data":
                form_data,

            "temporary_documents":
                temporary_documents
                or {},

            "email_verifications":
                email_verifications,

            "status":
                "pending",

            "created_by":
                created_by,

            "created_at":
                now,

            "updated_at":
                now,

            "expires_at":
                expires_at,
        }

        created = (
            pending_registration_repository
            .create(
                document
            )
        )

        if not created:
            raise ValueError(
                "Unable to start Customer "
                "verification."
            )

        return {
            "registration":
                created,

            # IMPORTANT:
            # Returned internally only so the caller
            # can send OTP emails.
            #
            # Never return plain_otps to frontend.
            "plain_otps":
                plain_otps,
        }

    # =====================================================
    # START VENDOR REGISTRATION
    # =====================================================

    @classmethod
    def start_vendor_registration(
        cls,
        form_data: dict,
        created_by: str,
        temporary_documents: dict | None = None,
    ) -> dict:

        registration_id = str(
            uuid.uuid4()
        )

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            now
            + timedelta(
                hours=
                    cls.OTP_VALID_HOURS
            )
        )

        email = str(
            form_data.get(
                "email",
                "",
            )
        ).strip()

        if not email:
            raise ValueError(
                "Vendor email is required."
            )

        (
            verification,
            otp,
        ) = (
            cls
            .build_email_verification(
                registration_id=
                    registration_id,

                email_key=
                    "vendor_email",

                email=
                    email,
            )
        )

        document = {
            "registration_id":
                registration_id,

            "entity_type":
                "vendor",

            "entity_name":
                str(
                    form_data.get(
                        "vendor_name",
                        "",
                    )
                    or ""
                ).strip(),

            "form_data":
                form_data,

            "temporary_documents":
                temporary_documents
                or {},

            "email_verifications": {
                "vendor_email":
                    verification,
            },

            "status":
                "pending",

            "created_by":
                created_by,

            "created_at":
                now,

            "updated_at":
                now,

            "expires_at":
                expires_at,
        }

        created = (
            pending_registration_repository
            .create(
                document
            )
        )

        if not created:
            raise ValueError(
                "Unable to start Vendor "
                "verification."
            )

        return {
            "registration":
                created,

            # Internal use only.
            "plain_otps": {
                "vendor_email":
                    otp,
            },
        }

    # =====================================================
    # VERIFY ONE EMAIL OTP
    # =====================================================

    @classmethod
    def verify_email_otp(
        cls,
        registration_id: str,
        email_key: str,
        otp: str,
    ) -> dict:

        registration = (
            pending_registration_repository
            .find_by_registration_id(
                registration_id
            )
        )

        if not registration:
            raise ValueError(
                "Pending registration "
                "not found."
            )

        if (
            registration.get(
                "status"
            )
            != "pending"
        ):
            raise ValueError(
                "Registration is no longer "
                "pending."
            )

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            registration.get(
                "expires_at"
            )
        )

        # MongoDB may return UTC datetimes
        # without timezone information.
        if (
                expires_at is not None
                and
                expires_at.tzinfo is None
        ):
            expires_at = (
                expires_at.replace(
                    tzinfo=timezone.utc
                )
            )

        if (
                expires_at is not None
                and
                expires_at <= now
        ):
            raise ValueError(
                "OTP has expired. "
                "Please request a new OTP."
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
                "Email verification "
                "not found."
            )

        if verification.get(
            "verified"
        ):
            return {
                "verified":
                    True,

                "already_verified":
                    True,
            }

        stored_hash = (
            verification.get(
                "otp_hash"
            )
        )

        if not stored_hash:
            raise ValueError(
                "OTP verification data "
                "is invalid."
            )

        if not cls.verify_otp_hash(
            registration_id=
                registration_id,

            email_key=
                email_key,

            otp=
                otp.strip(),

            stored_hash=
                stored_hash,
        ):
            raise ValueError(
                "Invalid OTP."
            )

        (
            pending_registration_repository
            .mark_email_verified(
                registration_id=
                    registration_id,

                email_key=
                    email_key,
            )
        )

        updated = (
            pending_registration_repository
            .find_by_registration_id(
                registration_id
            )
        )

        all_verified = all(
            item.get(
                "verified",
                False,
            )
            for item
            in updated.get(
                "email_verifications",
                {},
            ).values()
        )

        return {
            "verified":
                True,

            "email_key":
                email_key,

            "all_verified":
                all_verified,
        }

    def get_pending_registration(
            self,
            registration_id: str,
            user_id: str,
    ):
        registration = (
            pending_registration_repository
            .find_by_registration_id(
                registration_id
            )
        )

        if not registration:
            raise ValueError(
                "Pending registration not found."
            )

        if (
                registration.get(
                    "created_by"
                )
                != user_id
        ):
            raise ValueError(
                "You are not authorized to access "
                "this registration."
            )

        if (
                registration.get(
                    "status"
                )
                != "pending"
        ):
            raise ValueError(
                "Registration is no longer pending."
            )

        # ---------------------------------------------
        # CHECK 24-HOUR EXPIRY
        # ---------------------------------------------

        expires_at = (
            registration.get(
                "expires_at"
            )
        )

        if not expires_at:
            raise ValueError(
                "Registration expiry is missing."
            )

        now = datetime.now(
            timezone.utc
        )

        # MongoDB may contain an old naive datetime.
        if (
                expires_at.tzinfo
                is None
        ):
            expires_at = (
                expires_at.replace(
                    tzinfo=timezone.utc
                )
            )

        if now >= expires_at:
            raise ValueError(
                "Registration verification has expired."
            )

        # ---------------------------------------------
        # SAFE VERIFICATION FIELDS
        #
        # Never return otp_hash.
        # ---------------------------------------------

        verifications = (
            registration.get(
                "email_verifications",
                {},
            )
        )

        verification_fields = []

        labels = {
            "management_email":
                "Management Email",

            "accounts_email":
                "Accounts Email",

            "operations_email":
                "Operations Email",

            "vendor_email":
                "Vendor Email",
        }

        for (
                email_key,
                verification,
        ) in verifications.items():
            verification_fields.append(
                {
                    "key":
                        email_key,

                    "label":
                        labels.get(
                            email_key,
                            email_key,
                        ),

                    "email":
                        verification.get(
                            "email",
                            "",
                        ),

                    "verified":
                        verification.get(
                            "verified",
                            False,
                        ),
                }
            )

        return {
            "registration_id":
                registration[
                    "registration_id"
                ],

            "entity_type":
                registration[
                    "entity_type"
                ],

            "entity_name": (
    registration.get(
        "entity_name"
    )
    or registration.get(
        "form_data",
        {},
    ).get(
        "customer_name"
    )
    or registration.get(
        "form_data",
        {},
    ).get(
        "vendor_name"
    )
    or ""
),

            "status":
                registration[
                    "status"
                ],

            "expires_at":
                registration[
                    "expires_at"
                ],

            "verification_fields":
                verification_fields,

            # This lets frontend restore the form if needed.
            # OTP hashes are NOT inside form_data.
            "form_data":
                registration.get(
                    "form_data",
                    {},
                ),

            "has_gst_document":
                bool(
                    registration.get(
                        "temporary_documents",
                        {},
                    ).get(
                        "gst_document"
                    )
                ),

            "has_pan_document":
                bool(
                    registration.get(
                        "temporary_documents",
                        {},
                    ).get(
                        "pan_document"
                    )
                ),
        }

    def resend_otp(
            self,
            registration_id: str,
            email_key: str,
            user_id: str,
    ):
        registration = (
            pending_registration_repository
            .find_by_registration_id(
                registration_id
            )
        )

        if not registration:
            raise ValueError(
                "Pending registration not found."
            )

        if (
                registration.get(
                    "created_by"
                )
                != user_id
        ):
            raise ValueError(
                "You are not authorized to access "
                "this registration."
            )

        if (
                registration.get(
                    "status"
                )
                != "pending"
        ):
            raise ValueError(
                "Registration is no longer pending."
            )

        # ---------------------------------------------
        # CHECK 24-HOUR REGISTRATION EXPIRY
        # ---------------------------------------------

        expires_at = (
            registration.get(
                "expires_at"
            )
        )

        now = datetime.now(
            timezone.utc
        )

        if not expires_at:
            raise ValueError(
                "Registration expiry is missing."
            )

        if expires_at.tzinfo is None:
            expires_at = (
                expires_at.replace(
                    tzinfo=timezone.utc
                )
            )

        if now >= expires_at:
            raise ValueError(
                "Registration verification has expired."
            )

        # ---------------------------------------------
        # FIND REQUESTED EMAIL
        # ---------------------------------------------

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
                "Email verification field not found."
            )

        if verification.get(
                "verified",
                False,
        ):
            raise ValueError(
                "This email is already verified."
            )

        email_address = (
            verification.get(
                "email"
            )
        )

        if not email_address:
            raise ValueError(
                "Email address is missing."
            )

        # ---------------------------------------------
        # GENERATE NEW OTP
        # ---------------------------------------------

        otp = (
            self.generate_otp()
        )

        otp_hash = (
            self.hash_otp(
                registration_id=
                registration_id,

                email_key=
                email_key,

                otp=
                otp,
            )
        )

        # IMPORTANT:
        # Registration still expires at the original
        # 24-hour deadline.
        #
        # Resending OTP does NOT give another 24 hours.

        otp_expires_at = (
            min(
                now + timedelta(
                    minutes=15
                ),
                expires_at,
            )
            if expires_at is not None
            else now + timedelta(
                minutes=15
            )
        )

        # ---------------------------------------------
        # UPDATE ONLY THIS EMAIL'S OTP
        # ---------------------------------------------

        updated = (
            pending_registration_repository
            .update_email_verification(
                registration_id=
                registration_id,

                email_key=
                email_key,

                update_data={
                    "otp_hash":
                        otp_hash,

                    "otp_expires_at":
                        otp_expires_at,

                    "verified":
                        False,

                    "verified_at":
                        None,

                    "otp_sent_at":
                        now,
                },
            )
        )

        if not updated:
            raise ValueError(
                "Unable to update OTP."
            )

        return {
            "registration":
                registration,

            "email_key":
                email_key,

            "email":
                email_address,

            "otp":
                otp,

            "otp_expires_at":
                otp_expires_at,
        }


pending_registration_service = (
    PendingRegistrationService()
)