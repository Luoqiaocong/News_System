from datetime import timedelta, datetime
from typing import Optional
import re

from fastapi import HTTPException
from jose import jwt
from starlette import status

from Config.settings import settings
from hashids import Hashids

from Exception import UserException, ResponseCode
from models.User import User
import secrets


# ==========================================
# 核心函数 1：生成 Token (发证)
# ==========================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    生成 JWT 访问令牌
    :param data: 要存储在 Token 中的载荷 (例如 {"sub": str(user_id)})
    :param expires_delta: 可选的过期时间间隔
    """
    to_encode = data.copy()

    # 计算过期时间
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        # 如果没传，则使用 .env 中配置的默认时间
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 更新载荷中的 'exp' 字段（JWT 标准字段）
    to_encode.update({"exp": expire})

    # 使用私钥和算法进行签名加密
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(
        cur_pwd:str,
        user: User,
):
    # 校验旧密码
    if cur_pwd != user.password:
        raise UserException(code=ResponseCode.USER_PWD_AUTH_FAILED)


def validate_password_strength(password: str):
    if len(password) < 8:
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[0-9]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[a-z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[A-Z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'\"\\|,.<>/?]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)


hashids = Hashids(salt=settings.HASH_SALT, min_length=12)

def get_hashed_id(real_id: int) -> str:
    return hashids.encode(real_id)

def get_real_id(hashed_id: str) -> int:
    decoded = hashids.decode(hashed_id)
    if not decoded:
        raise HTTPException(status_code=400, detail="无效的 ID 格式")
    return decoded[0]


def create_refresh_token_urlsafe()->str:
    return secrets.token_urlsafe(64)


def create_refresh_token_hex()->str:
    return secrets.token_hex(32)
