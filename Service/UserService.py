from functools import wraps
import hashlib
from typing import Annotated, Any, Callable, Coroutine

from fastapi import Depends
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from Config.settings import settings
from Config.DataBaseConfig import get_db
from Exception import UserException, ResponseCode
from Repo import UserRepo
from Schemas.UserSchema import RegisterUserRequest, LoginUserRequest, UserProfileUpdate, \
    UserPwdAuth, UserPwdResetAuth
from Utils import SecurityUtil
from Utils.LogUtil import log
from Utils.AuthUtil import _manage_device_slots, create_access_token, create_refresh_token
from Utils.HashUtil import get_hashed_id
from Utils.FileUtil import upload_file
from models.User import User
from Utils.RedisUtil import redis_client
from Utils.TransactionMixin import TransactionMixin, transactional
from Utils.SecurityUtil import PasswordManager
from Utils.ServiceDecorator import HandlerServiceException


@HandlerServiceException
class UserService(TransactionMixin):
    _business_exception_type = UserException  # 注册为用户异常

    # 注入Repo和db，db是为了得在service层进行事务控制
    def __init__(
            self,
            repo: Annotated[UserRepo, Depends()],
            db: Annotated[AsyncSession, Depends(get_db)]  # 掌握事务主动权
    ):
        self.repo = repo
        self.db = db

    async def _get_user(self, *, email: str | None = None, user_id: int | None = None) -> User:
        user = await self.repo.get_user_dynamic(user_id=user_id, email=email)
        if not user:
            raise UserException(code=ResponseCode.USER_NOT_FOUND)
        return user

    async def _verify_code(self, email: str, code: str) -> None:
        key = f"user:verifyCode:{email}"
        stored_code = await redis_client.get(key)
        if stored_code != code:
            log.error(f"验证码不匹配，期望: {repr(stored_code)}, 收到: {repr(code)}")
            raise UserException(code=ResponseCode.CODE_VERIFY_FAILED)
        await redis_client.delete(key)  # 验证码一次性使用，验证成功后立即删除

    async def create_user(self, userdata: RegisterUserRequest):
        existing_user = await self.repo.get_user_dynamic(email=userdata.email)  # 先查数据库，确保邮箱唯一
        if existing_user:
            raise UserException(code=ResponseCode.USER_EXIST)

        # 密码强度校验
        SecurityUtil.validate_password_strength(userdata.password)

        # 验证码校验
        await self._verify_code(userdata.email, userdata.code)

        userdata.password = PasswordManager.hash(userdata.password)  # 密码哈希处理

        async with self.transaction_scope():  # 开启事务，确保用户创建和后续操作的原子性
            await self.repo.create(userdata)

    async def login_user(self, userdata: LoginUserRequest):
        user = await self.repo.login(userdata)

        if user is None or not PasswordManager.verify(userdata.password, user.password):
            raise UserException(code=ResponseCode.USER_LOGIN_FAILED)

        access_token = create_access_token({"sub": get_hashed_id(user.id)})

        refresh_token = create_refresh_token()
        
        # 多设备 3 槽位并发剪裁控制
        await _manage_device_slots(user.id, refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def logout_user(self, user_id: int, refresh_token: str):
        """用户主动退出登录：抹杀 Token，并拉入黑名单防重放"""
        rt_md5 = hashlib.md5(refresh_token.encode()).hexdigest()
        
        redis_list_key = f"user:refresh_tokens:{user_id}"  
        blacklist_key = f"token:blacklist:{rt_md5}"
        
        # 黑名单寿命：完美覆盖 AccessToken 的存活期（15分钟 + 5分钟容错）
        safe_blacklist_ttl = (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60) + 300

        #  从活跃设备列表中彻底剔除这台设备的 RefreshToken（剥夺继承权）
        await redis_client.lrem(redis_list_key, 0, rt_md5)  # 0 表示删除所有匹配项，理论上应该只有一个

        #  扔进黑名单，防止还没到期的旧 AccessToken 被前端 refresh 接口复活
        await redis_client.setex(blacklist_key, safe_blacklist_ttl, "logout")
    
    
    async def delete_user(self, user_email: str):
        user = await self._get_user(email=user_email)
        '''
        硬删除可能对用户操作不好，没有反悔机会，万一不小心注销了呢？
        所以得使用软删除，具体就是在数据库表中加入is_delete（置为True）、delete_time字段
        自动扫描数据库（FastAPI有这样的操作），当is_delete为True，delete_time时间也到了，那么就彻底删啦！
        '''
        async with self.transaction_scope():
            is_delete = await self.repo.delete(user.id)
        if not is_delete:
            log.error(f"'{user.email}'注销账户失败")
            raise UserException(code=ResponseCode.DATABASE_ERROR, msg="注销账户失败")
        log.info(f"'{user.email}'注销账户成功")

    async def update_user(self, user_update_info: dict[str, Any]):
        # 头像上传处理
        avatar_file, user_avatar = user_update_info['avatar'][0], user_update_info['avatar'][1]

        if avatar_file is not None:
            avatar_url = await upload_file(file_model="avatar", filepath=avatar_file)
        else:
            avatar_url = user_avatar

        user_update_data = UserProfileUpdate(
            nickname=user_update_info.get('nickname'),
            bio=user_update_info.get('bio'),
            avatar=HttpUrl(avatar_url) if avatar_url else user_avatar # 防止OSS上传失败导致的空字符串覆盖原有头像URL
        )

        async with self.transaction_scope():
            updated_user = await self.repo.update(
                user_update_info['email'],
                user_update_data.model_dump(exclude_none=True, exclude_unset=True)
            )

        if not updated_user:
            raise UserException(code=ResponseCode.USER_NOT_FOUND)
        
    async def update_user_password(self, pwd_data: UserPwdAuth, user: User):
        log.info(f"{user.email}请求修改密码")

        if not PasswordManager.verify(pwd_data.cur_pwd, user.password):
            raise UserException(code=ResponseCode.USER_PWD_AUTH_FAILED)

        if pwd_data.cur_pwd == pwd_data.new_pwd:
            raise UserException(code=ResponseCode.USER_PWD_SAME)

        SecurityUtil.validate_password_strength(pwd_data.new_pwd)

        async with self.transaction_scope():
            await self.repo.change_password(pwd_data.new_pwd, user)

        log.info(f"{user.email}修改密码成功")

    async def reset_user_password(self, user_request: UserPwdResetAuth):
        log.info(f"{user_request.email}请求重置密码")

        # 先校验密码强度，避免消耗验证码后失败
        SecurityUtil.validate_password_strength(user_request.new_pwd)

        await self._verify_code(user_request.email, user_request.code)
        user = await self._get_user(email=user_request.email)
        async with self.transaction_scope():
            await self.repo.change_password(user_request.new_pwd, user)
        log.info(f"{user.email}重置密码成功")
