from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.News import Category, News


async def get_categories(category_id:int|None,db: AsyncSession):

    stmt = select(Category).where(Category.id == category_id) if category_id else select(Category)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_news(db: AsyncSession,category_id:int,skip:int=0,limit:int=10):
    # 分别执行两个查询，但写法更简洁
    count_query = select(func.count(News.id)).where(News.category_id == category_id)
    count_result = (await db.execute(count_query)).scalar_one()
    if count_result == 0:
        return [], 0

    news_query = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    news_result = (await db.execute(news_query)).scalars().all()

    return news_result, count_result
