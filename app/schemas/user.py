import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, Field, model_validator

# Regex for validating strong passwords (at least 8 characters, 1 uppercase, 1 lowercase, 1 digit, 1 special char)
PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[\W_])[A-Za-z\d\W_]{8,}$"
# Regex for validating username (alphanumeric, no spaces, 4-20 characters)
USERNAME_REGEX = r"^[a-zA-Z0-9_]{4,}$"


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: str

    @field_validator('username')
    def validate_username(cls, v):
        if not re.match(USERNAME_REGEX, v):
            raise ValueError("Username must be alphanumeric, 4-20 characters, and cannot contain spaces.")
        return v

class UserLogin(BaseModel):
    username: str = Field(..., min_length=4, description="Username must be non-empty")
    password: str = Field(..., min_length=8, description="Password must be non-empty")

    @model_validator(mode="before")
    def validate_non_empty_fields(cls, values):
        username = values.get("username")
        password = values.get("password")
        if not username or not username.strip():
            raise ValueError("Username cannot be empty or whitespace.")
        if not password or not password.strip():
            raise ValueError("Password cannot be empty or whitespace.")
        return values


class UserCreate(UserBase):
    password: str

    @field_validator('password')
    def validate_password(cls, v):
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "Password must be at least 8 characters long, contain uppercase, lowercase, number, and special "
                "character.")
        return v


class UserUpdate(UserBase):
    password: Optional[str] = None

    @field_validator('password', mode='before')
    def validate_password(cls, v):
        if v and not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "Password must be at least 8 characters long, contain uppercase, lowercase, number, and special "
                "character.")
        return v


class UserInDBBase(UserBase):
    id: int
    is_active: bool
    organization_id: Optional[int] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass
