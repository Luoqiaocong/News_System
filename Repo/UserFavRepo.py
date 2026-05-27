from fastapi import Depends
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from Config.DataBaseConfig import get_db
from Exception.ResponseCode import ResponseCode
from Exception.BusinessException import UserFavException
from models.News import News
from models.UserNewsFavorite import UserFavorite


class UserFavRepo:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def add(self, news_id: int, user_id: int):
        fav = UserFavorite(user_id=user_id, news_id=news_id)
        try:
            self.db.add(fav)
            await self.db.flush()
        except IntegrityError:
            raise UserFavException(ResponseCode.FAVORITE_DUPLICATE)

    async def remove(self, news_ids: list[int], user_id: int):
        if not news_ids:
            return 0
        query = delete(UserFavorite).where(
            UserFavorite.news_id.in_(news_ids),
            UserFavorite.user_id == user_id
        )
        res = await self.db.execute(query)
        return res.rowcount # type: ignore

    async def get(self, user_id: int, page: int, page_size: int):
        count_query = select(func.count()).where(UserFavorite.user_id == user_id)
        total = (await self.db.execute(count_query)).scalar_one()

        query = (
            select(News, UserFavorite.favorited_at, UserFavorite.id.label("favorite_id"))
            .join(UserFavorite, UserFavorite.news_id == News.id)
            .where(UserFavorite.user_id == user_id)
            .order_by(UserFavorite.favorited_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        rows = (await self.db.execute(query)).all()
        return rows, total
    

    async def get_all(self,user_id:int):
        query = select(UserFavorite.news_id).where(UserFavorite.user_id == user_id)
        res = await self.db.execute(query)
        return set(row[0] for row in res.fetchall())

    async def delete_all(self, user_id: int):
        query = delete(UserFavorite).where(UserFavorite.user_id == user_id)
        res = await self.db.execute(query)
        return res.rowcount # type: ignore
