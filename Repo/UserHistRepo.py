from datetime import datetime

from fastapi import Depends
from sqlalchemy import update, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from models.News import News
from models.UserNewsHistory import UserNewsHistory


class UserHistRepo:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def add_view(self,news_id: int, user_id: int):
        
        now = datetime.now()

        # 先尝试更新已存在的记录
        stmt = (
            update(UserNewsHistory)
            .where(UserNewsHistory.user_id == user_id)
            .where(UserNewsHistory.news_id == news_id)
            .values(viewed_at=now)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0  # 如果更新了记录，返回 True

    async def add_hist(self,news_id:int,user_id:int):
        hist = UserNewsHistory(user_id=user_id, news_id=news_id, viewed_at=datetime.now())
        self.db.add(hist)
        await self.db.flush()  # 刷新以获取 hist.id

    async def delete_history(self,user_id:int,news_ids:list[int]):
        '''

        :param user_id:
        :param news_ids:
        :param self.db:
        :return:

        采用宽松模式，可部分删除
        '''
        if not news_ids:
            return 0
        query = delete(UserNewsHistory).where(UserNewsHistory.user_id == user_id,UserNewsHistory.news_id.in_(news_ids))
        res = await self.db.execute(query)
        await self.db.commit()
        return res.rowcount

    async def get_all_history(self,user_id:int,page:int,pagesize:int):
        count_query = select(func.count()).where(UserNewsHistory.user_id==user_id)
        total = (await self.db.execute(count_query)).scalar_one()

        query = (
            select(News,UserNewsHistory.viewed_at,UserNewsHistory.id.label("history_id"))
                    .join(UserNewsHistory,  UserNewsHistory.news_id==News.id)
                    .where(UserNewsHistory.user_id == user_id)
                    .order_by(UserNewsHistory.viewed_at.desc())
                    .offset((page-1)*pagesize).limit(pagesize))
        rows = (await self.db.execute(query)).all()
        return rows,total

    async def remove_all(self,user_id:int):
        query = delete(UserNewsHistory).where(UserNewsHistory.user_id == user_id)
        res = await self.db.execute(query)
        await self.db.commit()
        return res.rowcount