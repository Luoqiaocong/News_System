from typing import Any
from fastapi import  Depends
from sqlalchemy import  update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from Exception import ResponseCode
from Schemas.UserSchema import UserRequest, UserPwdResetAuth
from Exception.BusinessException import UserException
from Utils.LogUtil import log
from models.User import User

from sqlalchemy import select


class UserRepo:

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    # 基础查询逻辑可以复用
    async def _get_user_base(self, statement)-> User | None:
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str)-> User | None:
        return await self._get_user_base(select(User).where(User.email == email))

    async def get_by_id(self, user_id: int):
        # 使用主键查询最快的方式
        return await self.db.get(User, user_id)

    async def get_user_dynamic(self,user_id:int=None, email:str=None)-> User | None:
        if user_id: return await self.db.get(User, user_id) # 这里警告是IDE误报，正常也是返回一个User对象
        if email:return await self._get_user_base(select(User).where(User.email == email))
        return None

    async def create(self, userdata: UserRequest):
        user = User(email=userdata.email, password=userdata.password)
        self.db.add(user)
        await self.db.flush()  # 不作提交

    async def login(self, userdata: UserRequest):
        # 1. 先根据邮箱捞出用户
        stmt = select(User).where(User.email == userdata.email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        # 2. 逻辑判断
        if not user:
            return None

        if user.password != userdata.password:
            return None

        # 3. 验证成功
        return user

    async def set_token(self, user_id: int, token: str):
        # 无论之前是否有token，都换成新token
        query = update(User).where(User.id == user_id).values(token=token)
        await self.db.execute(query)
        await self.db.flush()

    async def update(self, email: str, user_update_data: dict[str, Any]) -> User | None:
        """更新用户信息并返回更新后的用户对象"""
        # 1. 查询用户是否存在
        user = await self.get_user_dynamic(email=email)
        if not user:
            return None

        # 2. 更新字段（ORM 方式，避免使用 Update 语句）
        for key, value in user_update_data.items():
            if hasattr(user, key):  # 判断user是否有这个key键
                setattr(user, key, value)  # 赋值

        # 3. flush 让 SQLAlchemy 同步到数据库（但不提交，由 Service 层控制事务）
        await self.db.flush()

        # 4. 返回更新后的用户对象（此时 user 已经是最新状态）
        return user

    async def delete(self, user_id: int):
        query = delete(User).where(User.id == user_id)
        row = await self.db.execute(query)
        await self.db.flush()
        return row.rowcount > 0

    async def change_password(self, new_pwd:str, user: User):
        user.password = new_pwd
        await self.db.flush()

    async def reset_password(self, user_request: UserPwdResetAuth):
        """
        重置用户密码
        """
        # 2. 执行更新
        query = update(User).where(User.email == user_request.email).values(password=user_request.new_pwd)
        res = await  self.db.execute(query)

        # 3. 检查是否找到用户
        if res.rowcount == 0:
            await  self.db.rollback()
            raise UserException(code=ResponseCode.USER_NOT_FOUND)

        # 4. 提交事务
        try:
            await  self.db.commit()
        except Exception as e:
            await  self.db.rollback()
            log.error(f"'{user_request.email}'重置密码失败，失败原因：{e}")
            raise UserException(code=ResponseCode.DATABASE_ERROR, msg="密码重置失败")



