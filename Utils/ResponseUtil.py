from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder  # 核心：用于解析模型和对象
from Exception.ResponseCode import ResponseCode

def base_response(
    status_code,
    code: int,
    message: str,
    data: Any = None,
) -> JSONResponse:
    """底层响应封装"""
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": jsonable_encoder(data)  # 自动处理 Pydantic/ORM/Datetime
        }
    )

def success_response(
    status_code: int = 200,
    success_code: ResponseCode = ResponseCode.SUCCESS,
    message: Optional[str] = None,
    data: Any = None,

) -> JSONResponse:
    """成功响应 - 默认返回 HTTP 200"""
    return base_response(
        status_code=status_code,
        code=success_code.code,
        message=message or success_code.message,
        data=data,
    )