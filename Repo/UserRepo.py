from typing import Any
from fastapi import  Depends
from sqlalchemy import  update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from Schemas.UserSchema import UserRequest
from models.User import User
from Utils.SecurityUtil import pwd_manager
from sqlalchemy import select


class UserRepo:

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    # 基础查询逻辑可以复用
    async def _get_user_base(self, statement)-> User | None:
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_dynamic(self,user_id:int|None=None, email:str|None=None)-> User | None: # type: ignore
        if user_id: return await self.db.get(User, user_id) # 这里警告是IDE误报，正常也是返回一个User对象
        if email:return await self._get_user_base(select(User).where(User.email == email))
        return None

    async def create(self, userdata: UserRequest):
        user = User(email=userdata.email, password=userdata.password)
        self.db.add(user)
        await self.db.flush()  # 不作提交

    async def login(self, userdata: UserRequest):
        stmt = select(User).where(User.email == userdata.email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not await pwd_manager.verify(userdata.password, user.password):
            return None

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
        return row.rowcount > 0 # type: ignore

    async def change_password(self, new_pwd:str, user: User):
        user.password = await pwd_manager.hash(new_pwd) # type: ignore
        await self.db.flush()

