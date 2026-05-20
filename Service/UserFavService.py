from contextlib import asynccontextmanager
from typing import Annotated
from Utils.LogUtil import log
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Config.DataBaseConfig import get_db
from Exception import ResponseCode
from Exception import BaseBusinessException, NewsException, UserFavException
from Repo import NewsRepo, UserFavCacheRepo, UserFavRepo
from Utils.ServiceDecorator import handle_service_exception


class UserFavService():
    def __init__(self,
                 repo: Annotated[UserFavRepo, Depends()],
                 db: Annotated[AsyncSession, Depends(get_db)]):
        self.repo = repo
        self.db = db

    @asynccontextmanager
    async def transaction_scope(self):
        try:
            yield
            await self.db.commit()
        except UserFavException:
            await self.db.rollback()
            raise
        except Exception as e:
            log.error(f"未捕获的系统异常: {e}")
            await self.db.rollback()
            raise BaseBusinessException(code=ResponseCode.DATABASE_ERROR)

    @handle_service_exception(pass_through_exceptions=(NewsException, UserFavException,))
    async def add_favorite(self, news_id: int, user_id: int):
        if not await NewsRepo.check_news_exists(news_id, self.db):  # 检查新闻是否存在
            raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)

        async with self.transaction_scope():
            await self.repo.add(news_id, user_id)  # 添加收藏记录

        await UserFavCacheRepo.add_fav_cache(news_id, user_id)

    @handle_service_exception(pass_through_exceptions=(NewsException,))
    async def remove_favorites(self, news_ids: list[int], user_id: int):
        count = await self.repo.remove(news_ids, user_id)
        return count

    async def check_favorite(self, news_id: int, user_id: int) -> bool:
        return await self.repo.check(news_id, user_id)

    async def get_favorites(self, user_id: int, page: int, page_size: int):
        return await self.repo.get(user_id, page, page_size)

    async def clear_favorites(self, user_id: int):
        return await self.repo.delete_all(user_id)
