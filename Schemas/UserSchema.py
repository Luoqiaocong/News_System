from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, EmailStr, field_serializer

from Utils.HashUtil import get_hashed_id


class UserIdentity(BaseModel):
    id: Annotated[int, Field(description="用户ID")]
    email: Annotated[EmailStr, Field(description="邮箱地址")]


class UserRequest(BaseModel):
    email: Annotated[EmailStr, Field(description="邮箱地址")]
    password: Annotated[str, Field(description="密码", min_length=8)]


class UserCodeIdentity(BaseModel):
    code: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        pattern=r"^\d{6}$", 
        description="6位纯数字邮件验证码"
    )


class RegisterUserRequest(UserRequest,UserCodeIdentity):
    nickname: Annotated[str, Field(description="昵称", min_length=2, max_length=10)]
    

class LoginUserRequest(UserRequest):
    confirm_restore: Annotated[bool, Field(description="是否确认恢复账户")] = False


class UserProfileBase(BaseModel):
    nickname: Annotated[str | None, Field(description="昵称", max_length=10)] = None
    avatar: Annotated[HttpUrl, Field(description="头像链接")] = None
    bio: Annotated[str | None, Field(description="个人简介", max_length=100)] = None


UserProfileUpdate = UserProfileBase


class UserInfo(UserIdentity, UserProfileBase):

    @field_serializer('id')
    def serialize_id(self, id: int, _info):
        return get_hashed_id(id)

    model_config = {"from_attributes": True}


class UserPwdAuth(BaseModel):
    cur_pwd: Annotated[str, Field(description="现密码", min_length=8)]
    new_pwd: Annotated[str, Field(description="新密码", min_length=8)]

    model_config = {
        "from_attributes": True,
    }


class UserPwdResetAuth(BaseModel):
    email: Annotated[EmailStr, Field(description="邮箱地址")]
    code: Annotated[str, Field(description="验证码")]
    new_pwd: Annotated[str, Field(description="新密码", min_length=8, alias="newPwd")]

class LogoutRequest(BaseModel):
    refresh_token: str

class DeleteAccountRequest(UserCodeIdentity):
    pass
      