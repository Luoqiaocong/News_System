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



# 实际上这一部分交给了全局异常处理，这个函数并没有实际被调用
def error_response(
        status_code: int = 400,
        error_code:ResponseCode = ResponseCode.PARAM_ERROR,
        message: Optional[str] = None,
        data: Any = None
) -> JSONResponse:
    """失败响应 - 也返回 HTTP 200，用业务 code 区分错误"""
    return base_response(
        status_code=status_code,
        code=error_code.code,
        message=message or error_code.message,
        data=data,
    )