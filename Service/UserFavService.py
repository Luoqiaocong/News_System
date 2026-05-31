from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Config.DataBaseConfig import get_db
from Exception import ResponseCode
from Exception import NewsException, UserFavException
from Repo import NewsRepo, UserFavCacheRepo, UserFavRepo
from Schemas.UserFavSchema import FavoriteNewsItem, UserFavResponse
from Utils.ServiceDecorator import HandlerServiceException
from Utils.TransactionMixin import TransactionMixin
from Utils.SchemaUtil import rows_to_schema

@HandlerServiceException
class UserFavService(TransactionMixin):
    _business_exception_type = UserFavException

    def __init__(self,
                 repo: Annotated[UserFavRepo, Depends()],
                 db: Annotated[AsyncSession, Depends(get_db)]):
        self.repo = repo
        self.db = db

    async def add_favorite(self, news_id: int, user_id: int):
        if not await NewsRepo.check_news_exists(news_id, self.db):
            raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)

        async with self.transaction_scope():
            await self.repo.add(news_id, user_id)

        await UserFavCacheRepo.add(news_id, user_id)   # 加入缓存

    async def remove_favorites(self, news_ids: list[int], user_id: int):
        async with self.transaction_scope():
            count = await self.repo.remove(news_ids, user_id)
        await UserFavCacheRepo.remove(news_ids, user_id)
        return count

    async def check_favorite(self, news_id: int, user_id: int) -> bool:
        if not await UserFavCacheRepo.exists(user_id):  # 如果在缓存中没有看见有收藏信息
            news_ids = await self.repo.get_all(user_id) #  获取用户所有收藏
            await UserFavCacheRepo.write(user_id, list(news_ids))  # 写进redis
        return await UserFavCacheRepo.is_member(news_id, user_id) # 判断在缓存中是否有收藏

    async def get_favorites(self, user_id: int, page: int, page_size: int):
        '''
        这里没有通过redis去获取所有收藏，
        一是我用的是sadd，他没有对新闻进行排序，无法进行分页
        二是即使我用zadd，考虑到用户收藏的新闻数量一般也不会很多，直接查数据库也不会有性能问题
        
        但最终有可能的话还是改zadd吧
        '''
        rows, total = await self.repo.get(user_id, page, page_size)
        items = rows_to_schema(FavoriteNewsItem, rows, ("favorited_at", "favorite_id"))
        return UserFavResponse(fav_lt=items, total=total)

    async def clear_favorites(self, user_id: int):
        async with self.transaction_scope():
            count = await self.repo.delete_all(user_id)
        await UserFavCacheRepo.remove_all(user_id)
        return count
