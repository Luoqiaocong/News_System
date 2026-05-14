from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from Exception import UserException, ResponseCode
from Repo import UserRepo
from Schemas.UserSchema import RegisterUserRequest, LoginUserRequest, UserInfo, UserProfileUpdate, \
    UserPwdAuth, UserPwdResetAuth
from Utils import SecurityUtil
from Utils.LogUtil import log
from Utils.SecurityUtil import create_access_token
from Utils.FileUtil import upload_file
from models.User import User
from Utils.RedisUtil import redis_client

'''
用户Service操作，掌握事务主动权
'''


class UserService:

    # 注入Repo和db，db是为了得在service层进行事务控制
    def __init__(
            self,
            repo: Annotated[UserRepo, Depends()],
            db: Annotated[AsyncSession, Depends(get_db)]  # 掌握事务主动权
    ):
        self.repo = repo
        self.db = db

    @asynccontextmanager
    async def transaction_scope(self):
        try:
            yield  # 这里会执行 async with 块内部的代码
            await self.db.commit()
        except UserException:
            await self.db.rollback()
            raise
        except Exception as e:
            log.error(f"未捕获的系统异常: {e}")
            await self.db.rollback()
            raise UserException(code=ResponseCode.DATABASE_ERROR)

    async def _search_user(self, *, user_id: int = None, email: str = None) -> User:
        """验证用户是否存在（通过邮箱），存在则返回用户对象"""
        user = await self.repo.get_user_dynamic(user_id=user_id, email=email)
        if not user:
            raise UserException(code=ResponseCode.USER_NOT_FOUND)
        return user

    async def _verify_code_and_get_user(self, email: str, code: str) -> User:
        """验证验证码并获取用户"""
        key = f"user:verifyCode:{email}"
        stored_code = await redis_client.get(key)
        if stored_code != code:
            log.error(f"期望-->{stored_code},收到-->{code}")
            raise UserException(code=ResponseCode.CODE_VERIFY_FAILED)

        # 校验成功立即删除
        await redis_client.delete(key)
        return await self._search_user(email=email)

    async def _perform_password_reset(self, user: User, new_password: str):
        """执行密码重置操作"""
        await self.repo.change_password(new_password, user)

    async def create_user(self, userdata: RegisterUserRequest):
        async with self.transaction_scope():
            existing_user = await self.repo.get_user_dynamic(email=userdata.email)
            if existing_user:
                raise UserException(code=ResponseCode.USER_EXIST)
            # 写入操作
            await self.repo.create(userdata)

    async def login_user(self, userdata: LoginUserRequest):
        async with self.transaction_scope():
            user = await self.repo.login(userdata)  # 统一鉴别，无论是 用户不存在/用户或密码错误 都一样返回
            if not user:
                raise UserException(code=ResponseCode.USER_PASSWORD_ERROR)

            # 取得新token
            new_token = create_access_token({"sub": SecurityUtil.get_hashed_id(user.id)})
            '''
            事实上jwt是无状态的，可以不存数据库，但是如果要实现黑名单，就得使用Redis；
            现在是为了调试，因为我客户端还没做
            如果需要存进Redis，也直接改repo层即可（但目前我觉得我这个系统可以不做）
        
            但是以后就使用无状态的jwt吗？这个不确定，可能得加自定义逻辑
            '''
            await self.repo.set_token(user.id, new_token)
        return new_token

    async def delete_user(self, user_email: str):
        async with self.transaction_scope():
            user = await self._search_user(email=user_email)
            # 删除操作
            '''
            硬删除可能对用户操作不好，没有反悔机会，万一不小心注销了呢？
            所以得使用软删除，具体就是在数据库表中加入is_delete（置为True）、delete_time字段
            自动扫描数据库（FastAPI有这样的操作），当is_delete为True，delete_time时间也到了，那么就彻底删啦！
            '''
            is_delete = await self.repo.delete(user.id)
            if not is_delete:
                log.error(f"'{user.email}'注销账户失败")
                raise UserException(code=ResponseCode.DATABASE_ERROR, msg="注销账户失败")
            log.info(f"'{user.email}'注销账户成功")

    async def update_user(self, user_update_info: dict[str, Any]):
        async with self.transaction_scope():
            # 头像上传处理
            avatar_file, user_avatar = user_update_info['avatar'][0], user_update_info['avatar'][1]

            avatar_url = await upload_file(
                file_model="avatar",
                filepath=avatar_file
            ) if avatar_file is not None else user_avatar

            user_update_data = UserProfileUpdate(
                nickname=user_update_info.get('nickname'),
                bio=user_update_info.get('bio'),
                avatar=HttpUrl(avatar_url) if avatar_url else user_avatar
            )

            updated_user = await self.repo.update(
                user_update_info['email'],
                user_update_data.model_dump(exclude_none=True, exclude_unset=True)
            )

            if not updated_user:
                raise UserException(code=ResponseCode.USER_NOT_FOUND)
            return UserInfo.model_validate(updated_user)

    async def update_user_password(self, pwd_data: UserPwdAuth, user: User):
        async with self.transaction_scope():
            log.info(f"{user.email}请求修改密码")
            SecurityUtil.verify_password(pwd_data.cur_pwd, user)
            await self._perform_password_reset(user, pwd_data.new_pwd)
            log.info(f"{user.email}修改密码成功")

    async def reset_user_password(self, user_request: UserPwdResetAuth):
        async with self.transaction_scope():
            log.info(f"{user_request.email}请求重置密码")
            user = await self._verify_code_and_get_user(user_request.email, user_request.code)
            await self._perform_password_reset(user, user_request.new_pwd)
            log.info(f"{user.email}重置密码成功")
