from datetime import datetime, timezone

from pymongo import ASCENDING

from backend.database.mongo import db
from backend.repositories.base_repository import (
    BaseRepository,
)


pending_registrations = db[
    "pending_registrations"
]


class PendingRegistrationRepository(
    BaseRepository
):

    def __init__(self):
        super().__init__(
            pending_registrations
        )

    # =====================================================
    # INDEXES
    # =====================================================

    def create_indexes(self):

        self.collection.create_index(
            [
                (
                    "registration_id",
                    ASCENDING,
                )
            ],
            unique=True,
            name=(
                "pending_registration_id_unique"
            ),
        )

        self.collection.create_index(
            [
                (
                    "entity_type",
                    ASCENDING,
                )
            ],
            name=(
                "pending_registration_entity_type"
            ),
        )

        self.collection.create_index(
            [
                (
                    "status",
                    ASCENDING,
                )
            ],
            name=(
                "pending_registration_status"
            ),
        )

        self.collection.create_index(
            [
                (
                    "expires_at",
                    ASCENDING,
                )
            ],
            name=(
                "pending_registration_expires_at"
            ),
        )

        self.collection.create_index(
            [
                (
                    "created_by",
                    ASCENDING,
                ),
                (
                    "entity_type",
                    ASCENDING,
                ),
                (
                    "status",
                    ASCENDING,
                ),
            ],
            name=(
                "pending_registration_user_lookup"
            ),
        )

    # =====================================================
    # GET BY REGISTRATION ID
    # =====================================================

    def find_by_registration_id(
        self,
        registration_id: str,
    ):

        return self.collection.find_one(
            {
                "registration_id":
                    registration_id,
            }
        )

    # =====================================================
    # FIND ACTIVE PENDING REGISTRATION
    #
    # Used when user returns later.
    # =====================================================

    def find_pending_by_user(
        self,
        created_by: str,
        entity_type: str,
    ):

        return self.collection.find_one(
            {
                "created_by":
                    created_by,

                "entity_type":
                    entity_type,

                "status":
                    "pending",
            },
            sort=[
                (
                    "created_at",
                    -1,
                )
            ],
        )

    # =====================================================
    # UPDATE REGISTRATION
    # =====================================================

    def update_registration(
        self,
        registration_id: str,
        update_data: dict,
    ):

        update_data[
            "updated_at"
        ] = datetime.now(
            timezone.utc
        )

        return self.collection.update_one(
            {
                "registration_id":
                    registration_id,
            },
            {
                "$set":
                    update_data,
            },
        )

    # =====================================================
    # MARK INDIVIDUAL EMAIL VERIFIED
    #
    # email_key examples:
    #
    # management_email
    # accounts_email
    # operations_email
    # vendor_email
    # =====================================================

    def mark_email_verified(
        self,
        registration_id: str,
        email_key: str,
    ):

        now = datetime.now(
            timezone.utc
        )

        return self.collection.update_one(
            {
                "registration_id":
                    registration_id,

                "status":
                    "pending",
            },
            {
                "$set": {
                    (
                        f"email_verifications."
                        f"{email_key}.verified"
                    ):
                        True,

                    (
                        f"email_verifications."
                        f"{email_key}."
                        f"verified_at"
                    ):
                        now,

                    "updated_at":
                        now,
                }
            },
        )

    # =====================================================
    # MARK COMPLETED
    # =====================================================

    def mark_completed(
        self,
        registration_id: str,
        entity_id: str,
    ):

        now = datetime.now(
            timezone.utc
        )

        return self.collection.update_one(
            {
                "registration_id":
                    registration_id,

                "status":
                    "pending",
            },
            {
                "$set": {
                    "status":
                        "completed",

                    "entity_id":
                        entity_id,

                    "completed_at":
                        now,

                    "updated_at":
                        now,
                }
            },
        )

    # =====================================================
    # FIND EXPIRED PENDING REGISTRATIONS
    #
    # Used by scheduler for the 24-hour internal alert.
    # =====================================================

    def find_expired_pending(
        self,
        now: datetime,
    ):

        return list(
            self.collection.find(
                {
                    "status":
                        "pending",

                    "expires_at": {
                        "$lte":
                            now,
                    },

                    "admin_notified_at": {
                        "$exists":
                            False,
                    },
                }
            )
        )

    # =====================================================
    # MARK ADMIN NOTIFIED
    #
    # Prevents repeated 24-hour alert emails.
    # =====================================================

    def mark_admin_notified(
        self,
        registration_id: str,
    ):

        now = datetime.now(
            timezone.utc
        )

        return self.collection.update_one(
            {
                "registration_id":
                    registration_id,

                "status":
                    "pending",
            },
            {
                "$set": {
                    "admin_notified_at":
                        now,

                    "updated_at":
                        now,
                }
            },
        )

    def update_email_verification(
            self,
            registration_id: str,
            email_key: str,
            update_data: dict,
    ):
        set_data = {
            (
                f"email_verifications."
                f"{email_key}."
                f"{key}"
            ):
                value

            for key, value
            in update_data.items()
        }

        set_data[
            "updated_at"
        ] = datetime.now(
            timezone.utc
        )

        result = (
            self.collection
            .update_one(
                {
                    "registration_id":
                        registration_id,

                    "status":
                        "pending",
                },
                {
                    "$set":
                        set_data,
                },
            )
        )

        return (
                result.matched_count
                > 0
        )


pending_registration_repository = (
    PendingRegistrationRepository()
)