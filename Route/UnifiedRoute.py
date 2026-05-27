import json
from fastapi.routing import APIRoute
from typing import Callable
from fastapi import Response, Request
from starlette.responses import JSONResponse

from Exception import ResponseCode
from Utils.ResponseUtil import success_response


CODE_MAP = {
    201: ResponseCode.CREATED,  # Created -> 创建成功
    204: ResponseCode.NO_CONTENT,  # No Content -> 删除成功
    200: ResponseCode.SUCCESS   # SUCCESS -> 通用成功
}

class UnifiedRoute(APIRoute):
    """
    统一响应拦截类：
    负责拦截所有该路由下的函数返回值，并统一格式化为 {"code": ..., "data": ..., "message": ...}
    """

    def get_route_handler(self) -> Callable:
        # 1. 获取 FastAPI 默认的处理器（它负责运行你的 register 函数并处理依赖注入）
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # 2. 运行你的业务函数（比如 register），获取它生成的响应
            response = await original_route_handler(request)

            # 3. 检查响应是否属于 JSONResponse 类型
            # FastAPI 默认会将你的 dict, list, None, {} 等返回值自动转为 JSONResponse
            if isinstance(response, JSONResponse):

                # 获取接口定义时指定的 HTTP 状态码（比如 @router.post(status_code=201)）
                http_status = response.status_code

                # 从映射表取业务 code，取不到则用默认 10000
                business_code = CODE_MAP.get(http_status, ResponseCode.SUCCESS)
                # 4. 解析响应体中的原始字节数据
                # 如果你的函数返回 None，这里解析出来就是 b'null'
                body_content = response.body.decode()

                # 将字节转为 Python 对象 (dict, list, 或 None)
                try:
                    data = json.loads(body_content) if body_content else None
                except json.JSONDecodeError:
                    # 如果解析失败（例如不是 JSON），则原样返回不进行包装
                    return response

                # 5. 判断是否需要包装
                # 情况 A: 数据是 None (比如你的 register 函数没写 return)
                # 情况 B: 数据是 dict 但里面没有 "code" (说明没被手动包装过)
                # 情况 C: 数据是 list (比如返回用户列表)
                if data is None or not (isinstance(data, dict) and "code" in data):
                    # 6. 调用你的工具函数 success_response 进行包装
                    # 如果 data 为 None，包装后会变成 {"code": 10000, "message": "成功", "data": null}
                    return success_response(data=data,success_code=business_code)

            # 7. 如果是其他类型的响应（如二进制流、HTML 等），直接原样返回，不做干预
            return response

        # 返回这个增强后的处理器给 FastAPI 框架使用
        return custom_route_handler