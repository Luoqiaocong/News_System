import functools
from typing import Tuple, Type, Callable
from fastapi import UploadFile
import hashlib
from Exception import  BaseBusinessException, ResponseCode
from Utils.LogUtil import log


async def calculate_md5(file: UploadFile):
    md5_hash = hashlib.md5()
    while chunk := await file.read(8192):
        md5_hash.update(chunk)
    await file.seek(0) # 指针归零
    return md5_hash.hexdigest()

def handle_service_exception(
    pass_through_exceptions: Tuple[Type[Exception], ...]):
    """
    Service 层异常处理装饰器

    用法：
    @handle_service_exception("获取新闻列表失败")
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except pass_through_exceptions:
                # 业务异常直接抛出，不做处理
                raise
            except Exception as e:
                log.error(f"函数 {func.__name__} 发生未预期异常: {e}", exc_info=True)
                raise BaseBusinessException(code=ResponseCode.INTERNAL_ERROR)
        return wrapper

    return decorator