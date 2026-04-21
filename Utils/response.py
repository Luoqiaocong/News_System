# Utils/response.py
from Schemas.Response import BaseResponse
from typing import Any, Optional, Dict, List, Union


def success(data: Optional[Any] = None, msg: str = "success", code: int = 200) -> BaseResponse:
    """成功响应"""
    return BaseResponse(code=code, msg=msg, data=data)


def error(msg: str, code: int = 400, data: Optional[Any] = None) -> BaseResponse:
    """错误响应"""
    return BaseResponse(code=code, msg=msg, data=data)

