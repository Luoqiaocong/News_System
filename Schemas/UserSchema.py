from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, EmailStr, field_serializer

from Utils.HashUtil import get_hashed_id


class UserIdentity(BaseModel):
    id: Annotated[int, Field(description="用户ID")]
    email: Annotated[EmailStr, Field(description="邮箱地址")]


class UserRequest(BaseModel):
    email: Annotated[EmailStr, Field(description="邮箱地址")]
    password: Annotated[str, Field(description="密码", min_length=8)]  # 密码以后要进行复杂化校验


class RegisterUserRequest(UserRequest):
    code: Annotated[str, Field(description="验证码")] = None


class LoginUserRequest(UserRequest):
    pass


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


class UserToken(BaseModel):
    token: Annotated[str, Field(description="登录凭证")] = None
    # userInfo: Annotated[UserInfo ,Field(..., alias="userInfo")]=None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class UserPwdAuth(BaseModel):
    cur_pwd: Annotated[str, Field(description="现密码",min_length=8)]
    new_pwd: Annotated[str, Field(description="新密码",min_length=8)]

    model_config = {
        "from_attributes": True,
    }


class UserPwdResetAuth(BaseModel):
    email: Annotated[EmailStr,Field(description="邮箱地址")]
    code: Annotated[str, Field(description="验证码")]
    new_pwd: Annotated[str, Field(description="新密码",min_length=8,alias="newPwd")]
