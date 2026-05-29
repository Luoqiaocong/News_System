import functools
from typing import Type, Callable

from Exception import BaseBusinessException, ResponseCode
from Utils.LogUtil import log




class HandlerServiceException:
    def __init__(self, *pass_through_exceptions: Type[Exception]):
        self.pass_through_exceptions = pass_through_exceptions

    def __call__(self, func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except self.pass_through_exceptions:
                raise
            except Exception as e:
                log.error(f"函数 {func.__name__} 发生未预期异常: {e}", exc_info=True)
                raise BaseBusinessException(code=ResponseCode.SERVER_ERROR)
        return wrapper
