import functools
import inspect
from typing import Type, Callable

from Exception import BaseBusinessException, ResponseCode
from Utils.LogUtil import log


def skip_auto_exception(func: Callable):
    """方法装饰器（免死金牌）：
    被打上该标记的公开 async 方法将被类装饰器自动放行，不套用任何异常捕获
    """
    func._skip_auto_exception = True
    return func


def HandlerServiceException(cls):
    """类装饰器：自动给所有公开 async 方法加上 @HandlerServiceException
    完美兼容 Python 描述符协议，支持白名单机制，防止方法绑定或多类继承时参数错位
    """
    exc_type = getattr(cls, '_business_exception_type', None)
    if not exc_type:
        return cls

    for name, method in list(vars(cls).items()):
        # 1. 严格过滤私有方法和魔术方法（如 __init__）
        if name.startswith('_'):
            continue
            
        # 2. 准确识别类中定义的异步协程函数
        if inspect.iscoroutinefunction(method):
            # 🌟 检查是否挂了免死金牌，如果是则放行，不打补丁
            if getattr(method, '_skip_auto_exception', False):
                continue
                
            # 3. 拿到被异常装饰器包装后的代理函数
            wrapped_func = HandlerFunctionException(exc_type)(method)
            
            # 🌟 核心修正：将其写回类属性，保持原有的描述符协议可流转性
            setattr(cls, name, wrapped_func)
            
    return cls


class HandlerFunctionException:
    def __init__(self, *pass_through_exceptions: Type[Exception]):
        # 允许传入多个放行异常类（如业务主动抛出的自定异常）
        self.pass_through_exceptions = pass_through_exceptions

    def __call__(self, func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except self.pass_through_exceptions:
                # 如果是预设的放行异常，直接原样向上抛出，让统一全局异常中间件去处理
                raise
            except Exception as e:
                # 针对所有未预料到的崩溃（如 Redis/MySQL 挂了、空指针、索引越界等）进行降级兜底
                log.error(f"函数 {func.__name__} 发生未预期异常: {e}", exc_info=True)
                raise BaseBusinessException(code=ResponseCode.SERVER_ERROR)
        return wrapper