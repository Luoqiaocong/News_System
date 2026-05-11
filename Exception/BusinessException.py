from typing import Any
from Exception.ResponseCode import ResponseCode


class BaseBusinessException(Exception):
    """业务异常基类"""
    def __init__(self, code: ResponseCode = ResponseCode.PARAM_ERROR, msg: str = None, data: Any = None):
        self.code = code.code if isinstance(code, ResponseCode) else code
        self.msg = msg or (code.message if isinstance(code, ResponseCode) else "未知错误")
        self.data = data
        super().__init__(self.msg)


class UserException(BaseBusinessException):
    """用户模块异常"""
    def __init__(self, code: ResponseCode = ResponseCode.USER_NOT_FOUND, msg: str = None, data: Any = None):
        super().__init__(code=code, msg=msg, data=data)


class NewsException(BaseBusinessException):
    """新闻模块异常"""
    def __init__(self, code: ResponseCode = ResponseCode.NEWS_NOT_FOUND, msg: str = None, data: Any = None):
        super().__init__(code=code, msg=msg, data=data)


class UserFavoriteException(BaseBusinessException):
    """收藏模块异常"""
    def __init__(self, code: ResponseCode = ResponseCode.FAVORITE_DUPLICATE, msg: str = None, data: Any = None):
        super().__init__(code=code, msg=msg, data=data)


class UserHistoryException(BaseBusinessException):
    """浏览历史模块异常"""
    def __init__(self, code: ResponseCode = ResponseCode.HISTORY_NOT_FOUND, msg: str = None, data: Any = None):
        super().__init__(code=code, msg=msg, data=data)
