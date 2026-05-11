from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class VerifyEmail(BaseModel):
    email: Annotated[EmailStr, Field(description="邮箱地址")]