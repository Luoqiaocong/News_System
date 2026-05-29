import json
from fastapi.routing import APIRoute
from typing import Callable
from fastapi import Response, Request
from starlette.responses import JSONResponse

from Exception import ResponseCode
from Utils.ResponseUtil import success_response

# 映射表：将 HTTP 标准状态码映射为符合你项目规范的业务逻辑状态码
CODE_MAP = {
    201: ResponseCode.CREATED,     # 201 Created -> 映射为业务规范中的创建成功码
    204: ResponseCode.NO_CONTENT,  # 204 No Content -> 映射为业务规范中的删除/空内容成功码
    200: ResponseCode.SUCCESS      # 200 OK -> 映射为通用成功码
}

class UnifiedRoute(APIRoute):
    """
    统一响应拦截类：
    继承自 FastAPI 核心路由组件 APIRoute。
    负责在业务函数执行完毕、响应返回给前端之前进行拦截，
    并将散乱的返回值全自动格式化为标准响应体：{"code": ..., "data": ..., "message": ...}
    """

    def get_route_handler(self) -> Callable:
        # 1. 重写父类方法，获取 FastAPI 默认的路由处理器。
        # 这个处理器非常关键，它底层负责了路由匹配、参数依赖注入（Depends）以及业务函数的安全调用
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # 2. 真正的拦截核心：在这里安全地等待并运行你的业务函数（如路由里的 async def 函数），
            # 获取它生成的标准 Response 响应对象
            response = await original_route_handler(request)

            # 3. 筛选拦截对象：我们只对 JSON 数据进行拦截包装。
            # 当你的路由函数返回 dict, list, Pydantic Model 或是 None 时，FastAPI 底层都会自动将其转化为 JSONResponse。
            if isinstance(response, JSONResponse):

                # 🌟 [关键优势]：获取接口在装饰器里定义时指定的 HTTP 状态码。
                # 例如：@router.post("/news", status_code=201)，这里就能拿到 201
                http_status = response.status_code

                # 依据映射表，将 HTTP 状态码转化为对应的内部业务 Code（如果未映射，则默认为通用成功 SUCCESS）
                business_code = CODE_MAP.get(http_status, ResponseCode.SUCCESS)
                
                # 4. 提取原始响应体内容：
                # response.body 拿到的是二进制字节数据（如 b'{"id": 1}' 或 b'null'）
                body_content = response.body.decode() # type: ignore

                # 将字节字符串反序列化为 Python 的原生数据对象 (dict, list, 或 None)
                try:
                    data = json.loads(body_content) if body_content else None
                except json.JSONDecodeError:
                    # 💡 【防御性编程】：如果响应体由于特殊原因无法被反序列化（例如强行返回了非标准文本），
                    # 则不强制包装，直接原样放行，防止系统抛出 500 崩溃异常。
                    return response

                # 5. 核心判断区：决定这个数据是否需要被“包一层壳”
                # 满足以下三大条件之一的，说明数据尚未被统一格式化，需要包装：
                # 情况 A: data is None (即业务接口没有写 return，或者返回了 None)
                # 情况 B: 数据是个字典，但是里面没有 "code" 键 (说明是普通的业务数据字典，不是手动包装过的对象)
                # 情况 C: 数据是个纯列表 list (例如返回新闻卡片列表：[{"id": 1}, {"id": 2}])
                if data is None or not (isinstance(data, dict) and "code" in data):
                    
                    # 6. 调用统一成功包装工具函数：
                    # 将剥离出来的 data 重新组装，并带入刚刚根据 HTTP 状态码推导出来的业务代码（business_code）。
                    # success_response 内部会将其重新打包成一个全新的 JSONResponse 并返回。

                    # 1. 现场生成新 Response 壳
                    new_response = success_response(data=data, success_code=business_code)
    
                    # 2. 🌟 灵魂移植 A：把原来路由挂载的后台任务（BackgroundTask）原封不动拷贝过来
                    new_response.background = response.background 
                    
                    # 3. 🌟 灵魂移植 B：把原响应的 HTTP 状态码和头信息也继承过来（防止丢掉跨域或自定义 Header）
                    new_response.status_code = response.status_code
                    # 排除掉原本的 Content-Length，因为重新打包后响应体大小变了，让新 Response 重新计算
                    for key, value in response.headers.items():
                        if key.lower() != "content-length":
                            new_response.headers[key] = value
                            
                    return new_response
            # 7. 纯流式/静态放行：如果响应对象属于 HTMLResponse、StreamingResponse（下载文件）等，
            # 或者是已经被手动包装好的响应，则直接原样返回，不进行任何额外干预。
            return response

        # 将这个我们亲手打造的、具备“自动打包功能”的增强型处理器返回给 FastAPI 框架，替代官方默认行为
        return custom_route_handler