from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Schemas.Users import UserRequest
from Utils.UserUtil import generate_token
from models.Users import User


async def search_user(db: AsyncSession, username: str):
    stmt = select(User).where(User.username == username)
    user_info = await db.execute(stmt)
    return user_info.scalar_one_or_none()


async def create_user(db: AsyncSession, userdata: UserRequest):
    user = User(username=userdata.username, password=userdata.password, token=generate_token())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
