from typing import Optional
from datetime import datetime
from fastapi import Depends
from sqlalchemy import and_, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from models.News import Category, News

class NewsRepo:
    def __init__(self,db:AsyncSession=Depends(get_db)):
        self.db = db

    async def get_categories(self, category_id: int=0):
        """
        获取新闻分类列表或单个分类详情。

        :param category_id: 分类ID，如果为0则获取所有分类，否则获取指定ID的分类
        :param db: 数据库会话
        :return: 分类对象列表
        """
        if category_id:
            category = await self.db.get(Category, category_id)  
            return [category] if category else []  # 返回单个分类的列表形式，方便统一处理
        return (await self.db.execute(select(Category))).scalars().all()  # 获取所有分类并返回列表

    async def get_news(self, category_id: int, skip: int = 0, limit: int = 10):
        count_query = select(func.count(News.id))
        news_query = select(News)
        if category_id:
            count_query = count_query.where(News.category_id == category_id)
            news_query = news_query.where(News.category_id == category_id)

        total = (await self.db.execute(count_query)).scalar_one()
        if total == 0:
            return [], 0

        rows = (await self.db.execute(news_query.offset(skip).limit(limit))).scalars().all()
        return rows, total

    async def get_news_detail(self,news_id: int):
        """
        获取新闻详情。
        :param news_id: 新闻ID
        :return: 新闻对象
        """
        # 构建查询语句
        stmt = select(News).where(News.id == news_id)
        result = (await self.db.execute(stmt)).scalar_one_or_none()

        # 如果新闻不存在，返回 None
        if not result:
            return None

        return result  # 返回 ORM 对象，Service 层负责转换为 Pydantic 模型

    async def update_views(self, news_id: int):
        """
        更新新闻的浏览量（加1）。

        :param news_id: 新闻ID
        :return: 布尔值，表示是否成功更新
        """
        # 执行更新操作，将浏览量加1
        stmt = (
            update(News)
            .where(News.id == news_id)
            .values(views=News.views + 1)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()

        # 返回是否更新成功（受影响的行数大于0表示成功）
        return result.rowcount > 0 # type: ignore

    async def get_related_news(self,news_id: int, category_id: int):
        """
        获取与指定新闻同分类的相关新闻列表（随机选取6条）。

        :param db: 数据库会话
        :param news_id: 当前新闻ID（排除自身）
        :param category_id: 分类ID
        :return: 相关新闻列表，每个元素为包含新闻基本信息的字典
        """
        # 构建查询语句：排除当前新闻，按分类筛选，随机排序，限制6条
        stmt = (
            select(News)
            .where(News.id != news_id, News.category_id == category_id)
            .order_by(func.rand())
            .limit(6)
        )
        result = await self.db.execute(stmt)

        return  result.scalars().all()

    @staticmethod
    async def check_news_exists(news_id:int,db:AsyncSession):
        """
        检查新闻是否存在。
        :param news_id: 新闻ID
        :return: 布尔值，表示新闻是否存在
        """
        stmt = select(func.count()).where(News.id == news_id)
        result = (await db.execute(stmt)).scalar_one_or_none()
        return result is not None
    
    async def get_all_news_ids(self, category_id: int):
        query = select(News.id)
        if category_id:
            query = query.where(News.category_id == category_id)
        query = query.order_by(News.publish_time.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search(self, query: str, category_id: int, start_date: Optional[str], end_date: Optional[str], offset: int, limit: int):
        filters = []
        if query:
            filters.append(News.title.like(f'%{query}%'))

        if category_id:
            filters.append(News.category_id == category_id) # type: ignore

        if start_date:
            filters.append(News.publish_time >= datetime.strptime(start_date, "%Y-%m-%d")) # type: ignore
        if end_date:
            filters.append(News.publish_time <= datetime.strptime(end_date, "%Y-%m-%d")) # type: ignore
        base = select(News).where(and_(*filters)) # 将 filters 列表中的所有条件用 AND 连接成 WHERE 子句
        total = (await self.db.execute(select(func.count()).select_from(base))).scalar_one() # type: ignore
        if total == 0:
            return [], 0
        rows = (await self.db.execute(base.order_by(News.publish_time.desc())
                .offset(offset).limit(limit))).scalars().all()  # offset(offset) → 跳过前 offset 条（用于分页）  limit(limit) → 只取 limit 条
        return rows, total 

        