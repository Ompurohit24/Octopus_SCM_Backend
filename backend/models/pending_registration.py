from pydantic import (
    BaseModel,
    Field,
)


class ResendRegistrationOTPRequest(
    BaseModel
):
    registration_id: str = Field(
        ...,
        min_length=1,
    )

    email_key: str = Field(
        ...,
        min_length=1,
    )