from typing import Annotated, Optional
from jose import JWTError, jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from Exception import UserException, ResponseCode
from Repo.UserRepo import UserRepo
from Config.settings import settings
from Utils.HashUtil import get_real_id
from models.User import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/user/login", auto_error=False)


# ==========================================
# 验证 Token (查证)
# ==========================================

# --- 1. 纯逻辑辅助函数 (不带 Depends，只接收实例) ---
async def _verify_token_logic(token: str, repo: UserRepo) -> Optional[User]:
    """
    解析 Token 并查询用户
    :param token: JWT 字符串
    :param repo: 已经由 FastAPI 注入好的 UserRepo 实例
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id:int = get_real_id(str(payload.get("sub")))
        if not user_id:
            return None
        # ✅ 使用注入好的 repo 实例执行查询
        return await repo.get_user_dynamic(user_id)
    except (JWTError, ValueError):
        return None


# --- 2. 可选登录依赖项 ---
async def get_current_user_optional(
        repo: Annotated[UserRepo, Depends()],
        token: Optional[str] = Depends(oauth2_scheme_optional)
) -> Optional[User]:
    if not token:
        return None
    # ✅ 手动将注入好的 repo 传给逻辑函数
    return await _verify_token_logic(token, repo)


# --- 3. 强制登录依赖项 (核心) ---
async def get_current_user(
        repo: Annotated[UserRepo, Depends()],  # ✅ 关键：在这里声明依赖，FastAPI 会自动注入
        token: str = Depends(oauth2_scheme),
) -> User:
    """
    强制用户认证

    FastAPI 执行流程：
    1. 从 Header 提取 token
    2. 实例化 UserRepo (并自动注入 db)
    3. 调用本函数
    """
    # ✅ 手动将注入好的 repo 传给逻辑函数
    user = await _verify_token_logic(token, repo)

    if not user:
        raise UserException(code=ResponseCode.TOKEN_EXPIRED)

    return user
