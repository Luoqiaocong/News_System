from typing import Annotated, Optional
from jose import ExpiredSignatureError, JWTError, jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from Exception import UserException, ResponseCode
from Repo.UserRepo import UserRepo
from Config.settings import settings
from Utils.HashUtil import get_real_id
from models.User import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/user/login", auto_error=False)


async def _verify_token_logic(token: str, repo: UserRepo) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise UserException(code=ResponseCode.TOKEN_EXPIRED)
    except JWTError:
        raise UserException(code=ResponseCode.TOKEN_INVALID)

    user_id = get_real_id(str(payload.get("sub")))
    if not user_id:
        raise UserException(code=ResponseCode.TOKEN_INVALID)

    user = await repo.get_user_dynamic(user_id)
    if not user:
        raise UserException(code=ResponseCode.TOKEN_INVALID)

    return user


async def get_current_user_optional(
        repo: Annotated[UserRepo, Depends()],
        token: Optional[str] = Depends(oauth2_scheme_optional)
) -> Optional[User]:
    if not token:
        return None
    try:
        return await _verify_token_logic(token, repo)
    except UserException:
        return None


async def get_current_user(
        repo: Annotated[UserRepo, Depends()],
        token: str = Depends(oauth2_scheme),
) -> User:
    return await _verify_token_logic(token, repo)
