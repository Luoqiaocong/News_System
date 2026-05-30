"""
异常处理模块
提供统一的业务异常类和响应码定义
"""

from Exception.ResponseCode import ResponseCode, get_response_info
from Exception.BusinessException import (
    BaseBusinessException,
    UserException,
    NewsException,
    UserFavException,
    UserHistException,
    AuthException
)

# __all__ 是 Python 模块中的一个特殊变量，它的作用是控制“白名单”。
# 具体来说，当你写 from Exception import *（导入所有东西）时，Python 只会导入 __all__ 列表里列出的这些名字。
__all__ = [
    "ResponseCode",
    "get_response_info",
    "BaseBusinessException",
    "UserException",
    "NewsException",
    "UserFavException",
    "UserHistException",
    "AuthException"

]
