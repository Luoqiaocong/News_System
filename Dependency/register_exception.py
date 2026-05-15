import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from Exception import BaseBusinessException, ResponseCode
from Utils.LogUtil import log


def register_exception(app: FastAPI):
    """
    全局异常注册函数
    """

    # 1. 处理业务逻辑异常
    @app.exception_handler(BaseBusinessException)
    async def unified_business_exception_handler(request: Request, exc: BaseBusinessException):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": exc.code,
                "message": exc.msg,
                "data": exc.data,
            }
        )

    # 2. 处理 FastAPI/Starlette 标准 HTTP 异常
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        error_code_map = {
            401: ResponseCode.UNAUTHORIZED,
            403: ResponseCode.FORBIDDEN,
            404: ResponseCode.NOT_FOUND,
            413: ResponseCode.FILE_TOO_LARGE,
            500: ResponseCode.INTERNAL_ERROR,
        }

        response_code = error_code_map.get(exc.status_code, ResponseCode.INTERNAL_ERROR)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": response_code.code,
                "message": exc.detail,
                "data": None
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # 1. 构造面向用户的简短消息 (取第一个错误)
        first_err = exc.errors()[0]
        field_name = str(first_err.get("loc")[-1])  # 拿到具体的字段名，如 "email"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": ResponseCode.PARAM_ERROR.code,
                "message": "Param Error",
                "data": f"{field_name}: {first_err.get('msg')}"  # 现在这是一个扁平的对象了
            }
        )

    # 4. 处理所有未捕获的系统异常
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error(f"捕获到未处理异常: {type(exc).__name__} - {exc}\n{traceback.format_exc()}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": ResponseCode.INTERNAL_ERROR.code,
                "message": "服务器开小差了，请稍后再试",
                "data": str(exc) if app.debug else None
            }
        )
