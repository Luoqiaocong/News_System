import time
from starlette.types import ASGIApp, Receive, Scope, Send
from Utils.LogUtil import log

class PerformanceMiddleware:
    """
    🌟 工业级纯净 ASGI 耗时统计中间件
    彻底免疫 BaseHTTPMiddleware 的 Content-Length 流冲突 Bug
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # 1. 过滤非 HTTP 请求（例如 WebSocket 或 Lifespan 系统事件直接放行）
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 2. 记录请求到达的物理时间
        start_time = time.time()
        
        # 3. 提取请求元数据（从 scope 中直接读取，速度极快，无需实例化 Request 对象）
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "")

        # 4. 核心：通过拦截底层 send 通道，在响应完全发射完毕的那一刻打印日志
        async def send_wrapper(message: dict) -> None:
            # http.response.body 带有 more_body=False 或者没有 more_body，说明响应体正式传输结束
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                process_time = time.time() - start_time
                log.info(f"[{method}] {path} - 耗时: {process_time:.4f}s")
            
            # 将原始消息原封不动地发给客户端，绝不污染或篡改数据流大小
            await send(message)

        # 5. 将包裹后的发送管道向下传递，驱动整个 FastAPI 路由链条
        await self.app(scope, receive, send_wrapper) # type: ignore