import json
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from Utils.LogUtil import log


class UnifiedResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # ✅ 1. 排除掉 Swagger 文档、静态文件或流式响应，避免干扰
        if request.url.path in ["/docs", "/openapi.json", "/favicon.ico"] or request.url.path.startswith("/static"):
            return await call_next(request)

        try:
            response = await call_next(request)
        except Exception as e:
            # 如果 call_next 本身报错（极少见），记录日志并返回 500
            log.error(f"中间件执行错误: {str(e)}")
            return JSONResponse(status_code=500, content={"code": 10501, "message": "服务器内部错误", "data": None})

        # ✅ 2. 只处理状态码为 200 且是 JSON 类型的响应
        if response.status_code == 200 and response.headers.get("content-type") == "application/json":
            # 提取响应体内容
            body_bytes = b""
            # 注意：response.body_iterator 只能遍历一次
            async for chunk in response.body_iterator:
                body_bytes += chunk

            try:
                original_data = json.loads(body_bytes.decode("utf-8"))

                # ✅ 3. 核心判断：如果返回的数据里没有 'code' 字段，说明还没被包装
                if not isinstance(original_data, dict) or "code" not in original_data:
                    wrapped_data = {
                        "code": 20000,
                        "message": "操作成功",
                        "data": original_data
                    }
                    return JSONResponse(content=wrapped_data, status_code=200)

            except json.JSONDecodeError:
                # 如果不是合法的 JSON，直接原样返回
                pass

            # 如果已经有 code 了，或者解析失败，重新构造一个 Response 返回原始数据
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        return response
