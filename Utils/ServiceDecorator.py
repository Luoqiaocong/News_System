import functools
from typing import Tuple, Type, Callable

from Exception import BaseBusinessException, ResponseCode
from Utils.LogUtil import log


def handle_service_exception(
    pass_through_exceptions: Tuple[Type[Exception], ...]):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except pass_through_exceptions:
                raise
            except Exception as e:
                log.error(f"函数 {func.__name__} 发生未预期异常: {e}", exc_info=True)
                raise BaseBusinessException(code=ResponseCode.SERVER_ERROR)
        return wrapper
    return decorator
