from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


class CustomerBase(BaseModel):

    customer_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    address: str

    # -------------------------------------------------
    # CUSTOMER EMAILS
    #
    # Customer can provide:
    #
    # - Management Email
    # - Accounts Email
    # - Operations Email
    #
    # At least ONE email is required.
    #
    # Later, OTP verification will be performed
    # independently for every entered email.
    # -------------------------------------------------

    management_email: Optional[
        EmailStr
    ] = None

    accounts_email: Optional[
        EmailStr
    ] = None

    operations_email: Optional[
        EmailStr
    ] = None

    countryCode: str = "+91"

    phone: str

    gstin: str

    gst_document: Optional[
        str
    ] = None

    pan: str

    pan_document: Optional[
        str
    ] = None

    tan: str

    # -------------------------------------------------
    # EMAIL VALIDATION
    #
    # At least one Customer email must exist.
    # -------------------------------------------------

    @model_validator(
        mode="after"
    )
    def validate_emails(
        self,
    ):

        if not any(
            [
                self.management_email,
                self.accounts_email,
                self.operations_email,
            ]
        ):
            raise ValueError(
                "At least one Customer email "
                "is required."
            )

        return self


class CustomerCreate(
    CustomerBase
):

    customer_code: Optional[
        str
    ] = None


class CustomerUpdate(
    BaseModel
):

    # -------------------------------------------------
    # PARTIAL UPDATE MODEL
    #
    # Do not inherit CustomerBase here.
    #
    # Update requests may contain only selected fields,
    # so all fields must remain optional.
    # -------------------------------------------------

    customer_name: Optional[
        str
    ] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    address: Optional[
        str
    ] = None

    management_email: Optional[
        EmailStr
    ] = None

    accounts_email: Optional[
        EmailStr
    ] = None

    operations_email: Optional[
        EmailStr
    ] = None

    countryCode: Optional[
        str
    ] = None

    phone: Optional[
        str
    ] = None

    gstin: Optional[
        str
    ] = None

    gst_document: Optional[
        str
    ] = None

    pan: Optional[
        str
    ] = None

    pan_document: Optional[
        str
    ] = None

    tan: Optional[
        str
    ] = None


class CustomerInDB(
    CustomerBase
):

    customer_code: str

    is_active: bool = True

    is_deleted: bool = False

    created_by: Optional[
        str
    ] = None

    updated_by: Optional[
        str
    ] = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )


class CustomerResponse(
    CustomerInDB
):

    id: str

    model_config = ConfigDict(
        from_attributes=True
    )