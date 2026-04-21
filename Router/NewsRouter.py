from typing import Annotated
from fastapi import Query, Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from Schemas.NewsSchema import NewsListResponse, NewsDetailResponse, CategoryResponse
from CRUD import NewsCRUD
from Config.settings import get_db
from Utils.response import success

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/categories")
async def get_categories(category_id: Annotated[int, Query(description="新闻类型id")] = None,
                         db: AsyncSession = Depends(get_db)):
    result = await NewsCRUD.get_categories(category_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="类型id不存在")

    return success(data=CategoryResponse(list=result))


@router.get("/list")
async def get_news(
        category_id: int = Query(..., description="新闻类型ID", alias="categoryId"),
        page: int = 1,
        pagesize: int = Query(10,lt=50, description="每页新闻数量", alias="pageSize"),
        db: AsyncSession = Depends(get_db)
):
    news_list, total = await NewsCRUD.get_news(db, category_id, (page - 1) * pagesize, pagesize)
    res = NewsListResponse(list=news_list, total=total)
    return success(data=res)

@router.get("/detail/{news_id}")
async def get_news_detail(news_id: int=Path(..., description="新闻ID"), db: AsyncSession = Depends(get_db)):
    news_detail = await NewsCRUD.get_news_detail(db, news_id)
    is_update = await NewsCRUD.update_views(db, news_id)
    if not news_detail or not is_update:
        raise HTTPException(status_code=404, detail="新闻不存在")
    related_news = await NewsCRUD.get_related_news(db, news_id,news_detail.category_id)

    res = NewsDetailResponse(list=news_detail, related_news=related_news)
    return success(data=res)
