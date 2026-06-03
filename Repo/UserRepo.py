from datetime import datetime, timedelta
from typing import Any
from fastapi import Depends
from sqlalchemy import update, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from Schemas.UserSchema import LoginUserRequest, RegisterUserRequest, UserRequest
from models.User import User
from Utils.SecurityUtil import PasswordManager


class UserRepo:

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    # 基础查询逻辑可以复用
    async def _get_user_base(self, statement, include_deleted: bool = False) -> User | None:
        if include_deleted:
            # 如果声明了需要穿透，就在语句上强行挂载特权信号
            statement = statement.execution_options(include_deleted=True)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_dynamic(
        self, 
        user_id: int | None = None, 
        email: str | None = None, 
        include_deleted: bool = False
    ) -> User | None:
        
        # 【分支 A】：通过 user_id 查询
        if user_id: 
            # 注意：self.db.get() 默认不支持直接挂载 execution_options。
            # 为了能够穿透查询被软删的 ID，统一用 select 语句改写，极其安全且标准
            stmt = select(User).where(User.id == user_id)
            return await self._get_user_base(stmt, include_deleted=include_deleted)
            
        # 【分支 B】：通过 email 查询
        if email:
            stmt = select(User).where(User.email == email)
            return await self._get_user_base(stmt, include_deleted=include_deleted)
            
        return None

    async def create(self, userdata: RegisterUserRequest):
        user = User(email=userdata.email, password=userdata.password, nickname=userdata.nickname,deleted_at=None)
        self.db.add(user)
        await self.db.flush()

    async def login(self, userdata: LoginUserRequest) -> User | None:
        stmt = select(User).where(User.email == userdata.email).execution_options(include_deleted=True)  # 登录查询必须穿透软删用户
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        return user if user is not None else None

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

    async def soft_delete(self, user_id: int):
        query = update(User).where(User.id == user_id).values(deleted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        row = await self.db.execute(query)
        await self.db.flush()
        return row.rowcount > 0 # type: ignore

    async def change_password(self, new_pwd: str, user: User):
        user.password = PasswordManager.hash(new_pwd)
        await self.db.flush()

    async def delete_user(self, user_email: str):
        stmt = delete(User).where(User.email == user_email)
        row = await self.db.execute(stmt)
        await self.db.flush()
        return row.rowcount > 0 # type: ignore

