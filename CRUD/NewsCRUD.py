from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.News import Category

async def get_categories(category_id:int|None,db: AsyncSession):

    stmt = select(Category).where(Category.id == category_id) if category_id else select(Category)

    result = await db.execute(stmt)
    return result.scalars().all()
