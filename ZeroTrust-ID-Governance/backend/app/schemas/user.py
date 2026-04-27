import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    employee_id: str
    username: str
    email: EmailStr
    display_name: str
    department: str | None = None
    user_type: str = "regular"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = None
    department: str | None = None
    user_type: str | None = None
    status: str | None = None
    account_expiry_date: date | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    status: str
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
