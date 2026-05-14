from fastapi import Depends
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from starlette import status

from Config.DataBaseConfig import get_db
from Repo import NewsRepo
from Exception.BusinessException import UserFavoriteException
from models.News import News
from models.UserNewsFavorite import UserFavorite


class UserFavoriteRepo:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

async def add_favorite(news_id:int,user_id:int,db:AsyncSession):
    await NewsRepo.get_news_detail(db,news_id)
    fav = UserFavorite(user_id = user_id,news_id=news_id)
    try:
        db.add(fav)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()

        raise UserFavoriteException(status_code=status.HTTP_409_CONFLICT,msg="您已收藏该新闻，请勿重新操作")


async def remove_favorite(news_ids:list[int],user_id:int,db:AsyncSession):
    if not news_ids :
        return 0
    query = delete(UserFavorite).where(UserFavorite.news_id.in_(news_ids),UserFavorite.user_id == user_id)
    res = await db.execute(query)
    await db.commit()
    return res.rowcount


async def check_is_favorite(news_id:int,user_id:int,db:AsyncSession):
    # 仅查询 1，不拉取整行模型对象
    query = select(UserFavorite).filter_by(user_id=user_id, news_id=news_id).limit(1)
    res = await db.execute(query)
    return res.scalar() is not None

async def get_all_favorites(user_id:int,page:int,page_size:int,db:AsyncSession):
    count_query = select(func.count()).where(UserFavorite.user_id==user_id)
    total = (await db.execute(count_query)).scalar_one()

    query=(select(News,UserFavorite.favorited_at,UserFavorite.id.label("favorite_id"))
            .join(UserFavorite,UserFavorite.news_id == News.id)
            .where(UserFavorite.user_id == user_id)
            .order_by(UserFavorite.favorited_at.desc())
            .offset((page-1)*page_size).limit(page_size)
            )
    rows=(await db.execute(query)).all()
    return rows,total

async def remove_all(user_id:int,db:AsyncSession):
    query=delete(UserFavorite).where(UserFavorite.user_id == user_id)
    res = await db.execute(query)
    await db.commit()
    return res.rowcount
