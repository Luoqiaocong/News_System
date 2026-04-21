from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Schemas.UsersSchema import UserRequest
from Utils.UserUtil import generate_token
from models.Users import User, UserToken


async def search_user(db: AsyncSession, userdata: UserRequest):
    stmt = select(User).where(User.username == userdata.username)
    user_info = await db.execute(stmt)
    return user_info.scalar_one_or_none()

async def verify_user(db: AsyncSession, userdata: UserRequest):
    stmt = select(User).where(User.username == userdata.username, User.password == userdata.password)
    user_info = await db.execute(stmt)
    return user_info.scalar_one_or_none()


async def create_user(db: AsyncSession, userdata: UserRequest):
    user = User(username=userdata.username, password=userdata.password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user



async def create_token(db: AsyncSession, user_id: int):
    # 1. 准备新数据
    new_token = generate_token()
    expire_at = datetime.now() + timedelta(days=7)

    # 2. 查找数据库中是否已存在该用户的 Token 记录
    # 注意：这里应该是 Token.user_id == user_id，确保查询对象正确
    result = await db.execute(select(UserToken).where(UserToken.user_id == user_id))
    token_record = result.scalar_one_or_none()

    if token_record:
        # 情况 A：找到旧记录 -> 直接更新已有对象的属性
        # SQLAlchemy 会自动追踪这些属性的变化
        token_record.token = new_token
        token_record.expire_at = expire_at
    else:
        # 情况 B：没找到记录 -> 创建新对象并添加到 Session
        token_record = UserToken(user_id=user_id, token=new_token, expire_at=expire_at)
        db.add(token_record)

    # 3. 统一提交并刷新数据
    # 无论上面走了哪个分支，最后只需执行一次 commit 即可确保数据落地
    await db.commit()
    await db.refresh(token_record)

    return new_token


