# Schemas/Response.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar  # ✅ 从原生 typing 导入
from typing import Optional, Any, Dict

# 创建一个泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    model_config ={
        "populate_by_name": True,
        "from_attributes": True,
        "extra": "allow"  # 允许额外字段
    }

    code: int = Field(200, description="响应状态码")
    msg: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
