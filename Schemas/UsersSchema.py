from pydantic import BaseModel, ConfigDict, Field


class UserRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    username: str
    nickname: str
    avatar: str
    bio: str|None = None


class UserAuthResponse(BaseModel):
    token:str | None = None
    userInfo: UserInfo =Field(..., alias="userInfo")

    model_config= ConfigDict(
        from_attributes=True,  # 允许从orm对象创建模型实例
        populate_by_name=True # alias/字段名兼容
    )