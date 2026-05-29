from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.password_policy import validate_password_strength
from app.schemas.user import UserPublicResponse


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublicResponse
