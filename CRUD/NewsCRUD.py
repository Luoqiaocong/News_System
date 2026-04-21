from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.News import Category, News


async def get_categories(category_id:int|None,db: AsyncSession):

    stmt = select(Category).where(Category.id == category_id) if category_id else select(Category).order_by(Category.id)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_news(db: AsyncSession,category_id:int,skip:int=0,limit:int=10):
    # 先查询新闻总数，如无数据则减少了一次查询，直接返回空列表和0
    count_query = select(func.count(News.id)).where(News.category_id == category_id)
    count_result = (await db.execute(count_query)).scalar_one()
    if count_result == 0:
        return [], 0

    news_query = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    news_result = (await db.execute(news_query)).scalars().all()

    return news_result, count_result


async def get_news_detail(db: AsyncSession,news_id:int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_views(db:AsyncSession,new_id:int):
    stmt = update(News).where(News.id==new_id).values(views=News.views+1)
    is_update = await db.execute(stmt)
    await db.commit()  # 确保数据被提交
    return is_update.rowcount>0   # 是否真的有数据被更新了


async def get_related_news(db: AsyncSession,news_id:int,category_id:int):
    # 查询相关新闻
    stmt = (
        select(News)
        .where(News.id != news_id, News.category_id == category_id)
        .order_by(func.rand())
        .limit(6)
    )
    result = await db.execute(stmt)
    return [{
             "id":item.id,
             "title":item.title,
             "author":item.author,
             "summary":item.summary,
             "thumbnail":item.thumbnail,
             "views":item.views,
             "category_id":item.category_id
             }for item in result.scalars().all()]  # 返回相关新闻列表
