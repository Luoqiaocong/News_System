from pydantic import BaseModel


class UserRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    model_config ={
        "populate_by_name": True,
        "from_attributes": True
    }

    username: str
    nickname: str
    avatar: str
    bio: str | None = None
    token: str | None = None