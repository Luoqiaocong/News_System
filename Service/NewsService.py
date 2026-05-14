import functools
import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated, Any, Callable
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from Config.DataBaseConfig import get_db
from Exception import NewsException, ResponseCode
from Repo import NewsRepo, UserHistoryRepo
from Schemas.NewsSchema import CategoryData, NewsData
from Schemas.UserSchema import UserInfo
from Utils.RedisUtil import redis_client, redis_cache_decorator
from Utils.LogUtil import log
from Utils.ResponseUtil import success_response


class NewsService:
    def __init__(self,
                repo: Annotated[NewsRepo, Depends()],
                db: Annotated[AsyncSession, Depends(get_db)]):
        self.repo = repo
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
    async def get_news_categories(self,category_id: int = None):
        categories_orm = await self.repo.get_categories(category_id)
        if not categories_orm:
            raise NewsException(code=ResponseCode.NEWS_CATEGORY_NOT_FOUND)

        return [CategoryData.model_validate(cat) for cat in categories_orm]


    async def get_news_list(self,category_id: int|None, page: int, page_size: int):

        # 1. 计算 Redis Zset 的切片索引范围
        # 比如 page=1, size=10 -> start=0, end=9 (正好是前10条数据)
        start = (page - 1) * page_size
        end = start + page_size - 1

        # 2. 动态拼接 Redis 中的 Zset Key
        # 如果 category_id 是 None，对应的就是 "news:list:all"
        if category_id is None:
            zset_key = "news:list:all"
        else:
            zset_key = f"news:list:{category_id}"

        # 3. 从 Zset 中按照分数（发布时间戳）由大到小（倒序）捞出新闻 ID 列表
        # zrevrange 是全异步操作
        news_ids = await redis_client.zrevrange(zset_key, start, end)

        # 如果缓存里什么都没捞到，说明这个分类下没新闻，或者分页已经越界了
        if not news_ids:
            return NewsException(code=ResponseCode.NEWS_NOT_FOUND)

        # 4. 批量获取这些新闻的详情数据（MGET 工业级并发利器）
        # 构造详情键列表：['news:detail:10', 'news:detail:9'...]
        detail_keys = [f"news:detail:{nid.decode('utf-8') if isinstance(nid, bytes) else nid}" for nid in news_ids]
        details = await redis_client.mget(*detail_keys)

        # 5. 解析并组装数据返回给前端
        news_list = []
        for detail in details:
            if detail:
                # Redis 拿出来的是字符串/字节流，反序列化为 Python 字典
                news_list.append(json.loads(detail))

        return news_list

    async def handle_news_view(
            self,
            db: AsyncSession,
            news_id: int,
            user: UserInfo
    ):
        """
        统一处理浏览逻辑：
        1. 增加浏览量 (核心逻辑)
        2. 如果有 user_id，记录历史 (附属逻辑)
        """
        # --- 1. 更新浏览量 (核心) ---
        success = await  self.repo.update_views(db, news_id)
        if not success:
            raise HTTPException(status_code=404, detail="该新闻不存在")

        # 立即提交浏览量，保住核心数据
        await db.commit()

        # --- 2. 记录历史 (附属) ---
        if user and user.id:
            try:
                await UserHistoryRepo.add_view(news_id, user.id, db)
                # 历史记录成功/更新后，提交历史记录的事务
                await db.commit()
            except Exception as e:
                # 万一发生其他意外（如数据库断开），确保回滚并静默
                await db.rollback()
                logging.error(f"\'{user.email}\'记录浏览历史失败，失败原因-->{e}")
