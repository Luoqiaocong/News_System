from datetime import datetime

from fastapi import Depends
from sqlalchemy import update, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from models.News import News
from models.UserNewsHistory import UserNewsHistory


class UserHistoryRepo:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

async def add_view(news_id: int, user_id: int, db: AsyncSession):
    now = datetime.now()

    # 先尝试更新已存在的记录
    stmt = (
        update(UserNewsHistory)
        .where(UserNewsHistory.user_id == user_id)
        .where(UserNewsHistory.news_id == news_id)
        .values(viewed_at=now)
    )
    result = await db.execute(stmt)

    # 如果没有更新任何行，说明记录不存在，需要插入
    if result.rowcount == 0:
        hist = UserNewsHistory(user_id=user_id, news_id=news_id, viewed_at=now)
        db.add(hist)
        await db.flush()


async def delete_history(user_id:int,news_ids:list[int],db:AsyncSession):
    '''

    :param user_id:
    :param news_ids:
    :param db:
    :return:

    采用宽松模式，可部分删除
    '''
    if not news_ids:
        return 0
    query = delete(UserNewsHistory).where(UserNewsHistory.user_id == user_id,UserNewsHistory.news_id.in_(news_ids))
    res = await db.execute(query)
    await db.commit()
    return res.rowcount


async def get_all_history(user_id:int,page:int,pagesize:int,db:AsyncSession):
    count_query = select(func.count()).where(UserNewsHistory.user_id==user_id)
    total = (await db.execute(count_query)).scalar_one()

    query = (
        select(News,UserNewsHistory.viewed_at,UserNewsHistory.id.label("history_id"))
                   .join(UserNewsHistory,  UserNewsHistory.news_id==News.id)
                   .where(UserNewsHistory.user_id == user_id)
                   .order_by(UserNewsHistory.viewed_at.desc())
                   .offset((page-1)*pagesize).limit(pagesize))
    rows = (await db.execute(query)).all()
    return rows,total

async def remove_all(user_id:int,db:AsyncSession):
    query = delete(UserNewsHistory).where(UserNewsHistory.user_id == user_id)
    res = await db.execute(query)
    await db.commit()
    return res.rowcount