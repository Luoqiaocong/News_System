from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from Exception.BusinessException import NewsException
from models.News import Category, News


async def get_categories(category_id: int | None, db: AsyncSession):
    """
    获取新闻分类列表或单个分类详情。
    
    :param category_id: 分类ID，如果提供则查询单个分类，否则查询所有分类
    :param db: 数据库会话
    :return: 分类对象列表
    :raises HTTPException: 当未查找到任何分类时抛出404错误
    """
    # 根据是否提供category_id构建不同的查询语句
    if category_id:
        stmt = select(Category).where(Category.id == category_id)
    else:
        stmt = select(Category).order_by(Category.id)

    result = (await db.execute(stmt)).scalars().all()

    # 如果结果为空，抛出404异常
    if not result:
        raise NewsException(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="未查找到新闻分类"
        )

    return result


async def get_news(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    """
    获取指定分类下的新闻列表及总数。
    
    :param db: 数据库会话
    :param category_id: 分类ID
    :param skip: 跳过的记录数（用于分页）
    :param limit: 返回的记录数（用于分页）
    :return: 包含新闻列表和总数的元组 (news_list, total_count)
    """
    # 先查询新闻总数，如无数据则减少一次查询，直接返回空列表和0
    count_query = select(func.count(News.id)).where(News.category_id == category_id)
    count_result = (await db.execute(count_query)).scalar_one()
    
    if count_result == 0:
        return [], 0

    # 构建分页查询语句
    news_query = (
        select(News)
        .where(News.category_id == category_id)
        .offset(skip)
        .limit(limit)
    )
    news_result = (await db.execute(news_query)).scalars().all()

    return news_result, count_result


async def get_news_detail(db: AsyncSession, news_id: int):
    """
    获取新闻详情。
    
    :param db: 数据库会话
    :param news_id: 新闻ID
    :return: 新闻对象
    :raises HTTPException: 当新闻不存在时抛出404错误
    """
    # 构建查询语句
    stmt = select(News).where(News.id == news_id)
    result = (await db.execute(stmt)).scalar_one_or_none()
    
    # 如果新闻不存在，抛出404异常
    if not result:
        raise NewsException(status_code=404, msg="新闻不存在")

    # 刷新对象以确保获取最新数据
    await db.refresh(result)

    return result


async def update_views(db: AsyncSession, news_id: int):
    """
    更新新闻的浏览量（加1）。
    
    :param db: 数据库会话
    :param news_id: 新闻ID
    :return: 布尔值，表示是否成功更新
    """
    # 执行更新操作，将浏览量加1
    stmt = (
        update(News)
        .where(News.id == news_id)
        .values(views=News.views + 1)
    )
    result = await db.execute(stmt)
    
    # 返回是否更新成功（受影响的行数大于0表示成功）
    return result.rowcount > 0


async def get_related_news(db: AsyncSession, news_id: int, category_id: int):
    """
    获取与指定新闻同分类的相关新闻列表（随机选取6条）。
    
    :param db: 数据库会话
    :param news_id: 当前新闻ID（排除自身）
    :param category_id: 分类ID
    :return: 相关新闻列表，每个元素为包含新闻基本信息的字典
    """
    # 构建查询语句：排除当前新闻，按分类筛选，随机排序，限制6条
    stmt = (
        select(News)
        .where(News.id != news_id, News.category_id == category_id)
        .order_by(func.rand())
        .limit(6)
    )
    result = await db.execute(stmt)
    
    # 将结果转换为字典列表返回
    return [
        {
            "id": item.id,
            "title": item.title,
            "author": item.author,
            "summary": item.summary,
            "thumbnail": item.thumbnail,
            "views": item.views,
            "category_id": item.category_id
        }
        for item in result.scalars().all()
    ]
