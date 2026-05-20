from datetime import datetime
import functools
import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated, Callable, Optional, Type, Tuple
from fastapi import HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from Config.DataBaseConfig import get_db
from Exception import NewsException, ResponseCode
from Repo import NewsRepo, NewsCacheRepo, UserHistRepo
from Schemas.NewsSchema import CategoryData, NewsData, NewsDetailResponse, NewsListResponse, NewsListCard, RelatedNewsCard
from Schemas.UserSchema import UserInfo
from Utils.ServiceDecorator import handle_service_exception
from Utils.RedisUtil import redis_cache_decorator
from Utils.LogUtil import log
from models.UserNewsHistory import UserNewsHistory


class NewsService:
    def __init__(self,
                repo: Annotated[NewsRepo, Depends()],
                Histrepo:Annotated[UserHistRepo, Depends()],
                db: Annotated[AsyncSession, Depends(get_db)]):
        self.repo = repo
        self.histrepo = Histrepo
        self.db = db

    @asynccontextmanager
    async def transaction_scope(self):
        try:
            yield  # 这里会执行 async with 块内部的代码
            await self.db.commit()
        except NewsException:
            await self.db.rollback()
            raise
        except Exception as e:
            log.error(f"未捕获的系统异常: {e}")
            await self.db.rollback()
            raise NewsException(code=ResponseCode.DATABASE_ERROR)

    @redis_cache_decorator(
        key_prefix="news:categories:{category_id}",
        expire=7200,
    )
    async def get_news_categories(self,category_id: Annotated[Optional[int], Query()] = None) -> list[CategoryData]:
        categories_orm = await self.repo.get_categories(category_id)
        if not categories_orm:
            raise NewsException(code=ResponseCode.NEWS_CATEGORY_NOT_FOUND)

        return [CategoryData.model_validate(cat) for cat in categories_orm]

    @handle_service_exception(pass_through_exceptions=(NewsException,)) # 捕获 NewsException，其他异常交由全局异常处理器
    async def get_news_list(self,category_id: int|None, page: int, page_size: int)->NewsListResponse:
        # 计算分页索引
        start = (page - 1) * page_size
        end = start + page_size - 1
    
        news_detail_lt,total = await NewsCacheRepo.get_news_list_cache(category_id,start,end)
        if not news_detail_lt or not total:
            raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)
        return NewsListResponse(
            news_list=[NewsListCard.model_validate(json.loads(detail)) for detail in news_detail_lt if detail],
            total=total)

    @handle_service_exception(pass_through_exceptions=(NewsException,)) # 捕获 NewsException，其他异常交由全局异常处理器
    async def get_news_detail(self, news_id:int):
        # ====== 1. 新闻详情（先缓存，后 DB）======
        detail_dict = await NewsCacheRepo.get_detail_cache(news_id)
        if detail_dict:
            # 缓存命中
            category_id = detail_dict.get("category_id")  # 从缓存中获取 category_id，后续获取相关新闻会用到
        else:
            # 缓存未命中，走 DB
            detail_orm = await self.repo.get_news_detail(news_id)
            if not detail_orm:
                raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)  
            category_id = detail_orm.category_id  # 从 DB 获取 category_id
            detail_dict = NewsData.model_validate(detail_orm).model_dump()  # 转 dict 写回缓存，避免重复序列化
            # 写回缓存
            await NewsCacheRepo.set_detail_cache(news_id, detail_dict)

        # ====== 2. 相关新闻（先 Redis Set SRANDMEMBER，后 DB ORDER BY RAND()）======
        related = await NewsCacheRepo.get_related_news_cache(category_id, news_id)
        if not related :
            # 缓存未命中，走 DB
            related = await self.repo.get_related_news(news_id, category_id)
            # 用刚取到的新闻 ID 增量预热 Set，不额外查全表
            related_ids = [i.id for i in related]
            if related_ids:
                await NewsCacheRepo.warm_related_news(category_id, related_ids)

        # ====== 3. 打包返回 ======
        return NewsDetailResponse(detail=NewsData.model_validate(detail_dict),related_news=[RelatedNewsCard.model_validate(r) for r in related])
    

    @handle_service_exception(pass_through_exceptions=(NewsException,)) # 捕获 NewsException，其他异常交由全局异常处理器
    async def handle_news_view(
            self,
            news_id: int,
            user:UserInfo
    ):
        """
        统一处理浏览逻辑：
        1. 增加浏览量 (核心逻辑)
        2. 如果有 user_id，记录历史 (附属逻辑)
        """
        # --- 1. 更新浏览量 (核心) ---
        success = await  self.repo.update_views(news_id)
        if not success:
            raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)

        # 立即提交浏览量，保住核心数据
        await self.db.commit()

        # 同步刷新 Redis 缓存中的浏览量，避免下次请求返回旧值
        await NewsCacheRepo.bump_views_cache(news_id)

        async with self.transaction_scope():
            # --- 2. 记录历史 (附属) ---
            if user and user.id:
                is_add = await self.histrepo.add_view(news_id, user.id)
                if not is_add:
                    await self.histrepo.add_hist(news_id, user.id)  # 新增调用 add_hist方法，确保记录存在



