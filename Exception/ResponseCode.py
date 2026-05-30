from enum import Enum

"""
业务错误码定义规范：
- 20000: 成功
- 1xxxx: 通用错误
- 2xxxx: 用户模块
- 3xxxx: 新闻模块
- 4xxxx: 收藏模块
- 5xxxx: 浏览历史模块
"""


class ResponseCode(Enum):
    """
    统一响应码枚举
    格式: (code, message)
    """

    # ========== 通用成功状态 ==========
    SUCCESS = (20000, "ok")
    CREATED = (20100, "操作成功")
    NO_CONTENT = (20400, "操作成功")

    # ========== 通用错误 (1xxxx) ==========
    PARAM_ERROR = (10001, "参数错误")
    PARAM_MISSING = (10002, "缺少必要参数")
    PARAM_INVALID = (10003, "参数格式不正确")
    FILE_TOO_LARGE = (10004, "文件大小超过限制")
    CODE_VERIFY_FAILED = (10005, "验证码验证失败")
    SERVER_ERROR = (10006, "服务器开小差了，请稍后尝试")


    UNAUTHORIZED = (10101, "未授权，请先登录")
    TOKEN_EXPIRED = (10102, "登录已过期，请重新登录")
    TOKEN_INVALID = (10103, "无效的令牌")
    FORBIDDEN = (10104, "禁止访问")
    PERMISSION_DENIED = (10105, "权限不足")

    NOT_FOUND = (10201, "资源不存在")
    RESOURCE_EXISTS = (10202, "资源已存在")
    CONFLICT = (10203, "操作冲突")

    INTERNAL_ERROR = (10501, "服务器内部错误")
    SERVICE_UNAVAILABLE = (10502, "服务暂时不可用")
    DATABASE_ERROR = (10503, "数据库操作失败")

    # ========== 用户模块 (2xxxx) ==========
    USER_NOT_FOUND = (20001, "用户不存在")
    USER_EXIST = (20002, "用户已存在")
    USER_LOGIN_FAILED = (20003, "用户名或密码错误")
    USER_ACCOUNT_DISABLED = (20004, "账户已被禁用")
    USER_REGISTER_FAILED = (20005, "注册失败，请稍后重试")
    USER_DELETE_FAILED = (20006, "注销失败，请稍后重试")
    USER_PWD_AUTH_FAILED = (20007, "密码验证失败")
    USER_PWD_NOSET = (20008, "密码未设置")
    USER_PWD_EMPTY = (20009, "密码不能为空")
    USER_PWD_WEAK = (20010, "密码需包含数字、大小写字母、特殊字符且至少8位")
    USER_PWD_SAME = (20011, "新密码不能与当前密码相同")

    # ========== 新闻模块 (3xxxx) ==========
    NEWS_NOT_FOUND = (30001, "新闻不存在")
    NEWS_CREATE_FAILED = (30002, "新闻创建失败")
    NEWS_UPDATE_FAILED = (30003, "新闻更新失败")
    NEWS_DELETE_FAILED = (30004, "新闻删除失败")
    NEWS_PUBLISH_FAILED = (30005, "新闻发布失败")
    NEWS_CATEGORY_NOT_FOUND = (30006, "新闻分类不存在")

    # ========== 收藏模块 (4xxxx) ==========
    FAVORITE_DUPLICATE = (40001, "您已收藏该新闻，请勿重复操作")
    FAVORITE_NOT_FOUND = (40002, "收藏记录不存在")
    FAVORITE_FAILED = (40003, "收藏操作失败")

    # ========== 浏览历史模块 (5xxxx) ==========
    HISTORY_NOT_FOUND = (50001, "浏览记录不存在")
    HISTORY_RECORD_FAILED = (50002, "记录浏览历史失败")

    @property
    def code(self) -> int:
        """获取错误码"""
        return self.value[0]

    @property
    def message(self) -> str:
        """获取错误信息"""
        return self.value[1]


def get_response_info(res_code: ResponseCode):
    """便捷获取码和信息的工具函数"""
    return res_code.code, res_code.message