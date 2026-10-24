from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _validate_bcrypt_password_length(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("password must be at most 72 UTF-8 bytes")
    return password


class UserRegister(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, password: str) -> str:
        return _validate_bcrypt_password_length(password)


class UserLogin(BaseModel):
    phone: str | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z][a-zA-Z0-9._-]{2,31}$",
    )
    password: str

    @model_validator(mode="after")
    def exactly_one_identifier(self):
        if (self.phone is None) == (self.username is None):
            raise ValueError("provide either phone or username")
        if self.username is not None:
            self.username = self.username.strip().lower()
        return self

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, password: str) -> str:
        return _validate_bcrypt_password_length(password)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    username: str | None = None
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
