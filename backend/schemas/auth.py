from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    role: Literal["USER", "ANALYST", "ADMIN"] = "USER"


class UserLogin(BaseModel):
    phone: str
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
