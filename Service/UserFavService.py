from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Config.DataBaseConfig import get_db
from Exception import ResponseCode
from Exception import BaseBusinessException, NewsException, UserFavException
from Repo import NewsRepo, UserFavCacheRepo, UserFavRepo
from Schemas.UserFavSchema import FavoriteNewsItem, UserFavResponse
from Utils.LogUtil import log


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

    
    async def add_favorite(self, news_id: int, user_id: int):
        if not await NewsRepo.check_news_exists(news_id, self.db):
            raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)

        async with self.transaction_scope():
            await self.repo.add(news_id, user_id)

        await UserFavCacheRepo.add(news_id, user_id)

    async def remove_favorites(self, news_ids: list[int], user_id: int):
        async with self.transaction_scope():
            count = await self.repo.remove(news_ids, user_id)
        await UserFavCacheRepo.remove(news_ids, user_id)
        return count

    async def check_favorite(self, news_id: int, user_id: int) -> bool:
        if not await UserFavCacheRepo.exists(user_id):
            news_ids = await self.repo.get_all(user_id)
            await UserFavCacheRepo.write(user_id, list(news_ids))
        return await UserFavCacheRepo.is_member(news_id, user_id)

    async def get_favorites(self, user_id: int, page: int, page_size: int):
        '''
        这里没有通过redis去获取所有收藏，
        一是我用的是sadd，他没有对新闻进行排序，无法进行分页
        二是即使我用zadd，考虑到用户收藏的新闻数量一般也不会很多，直接查数据库也不会有性能问题
        '''
        rows,total =  await self.repo.get(user_id, page, page_size)  
        
        '''
        这里解包再理解一下，或还有没有别的方法解包呢
        '''
        items = [
        FavoriteNewsItem.model_validate({
            # 1. 巧妙地把 SQLAlchemy 对象的字段直接扒成字典
            # 这样就避开了不能直接 **news_obj 的问题
            **{c.name: getattr(news_obj, c.name) for c in news_obj.__table__.columns},
            
            # 2. 把另外两个单独查出来的收藏字段拼进去
            # 因为开了 populate_by_name=True，这里直接写下划线类变量名，Pydantic 会自动认领
            "favorite_id": favorite_id,
            "favorited_at": favorited_at
        })
        for news_obj, favorited_at, favorite_id in rows
    ]
        return UserFavResponse(fav_lt=items, total=total)

    async def clear_favorites(self, user_id: int):
        async with self.transaction_scope():
            count = await self.repo.delete_all(user_id)
        await UserFavCacheRepo.remove_all(user_id)
        return count
