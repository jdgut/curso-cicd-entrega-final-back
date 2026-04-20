from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.domain import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.USER

    @field_validator("email")
    @classmethod
    def validate_domain(cls, value: EmailStr) -> EmailStr:
        if not str(value).endswith("@eafit.edu.co"):
            raise ValueError("Solo se permiten correos con dominio @eafit.edu.co")
        return value


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
