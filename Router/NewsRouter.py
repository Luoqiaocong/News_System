from typing import Annotated
from fastapi import Query

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from CRUD import NewsCRUD
from Config.settings import get_db

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/categories")
async def get_categories(category_id: Annotated[int, Query(description="新闻类型id")] = None,
                         db: AsyncSession = Depends(get_db)):
    result = await NewsCRUD.get_categories(category_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="类型id不存在")

    return result


@router.get("/list")
async def get_news(
        category_id: int = Query(..., description="新闻类型ID", alias="categoryId"),
        page: int = 1,
        pagesize: int = Query(10,lt=50, description="每页新闻数量", alias="pageSize"),
        db: AsyncSession = Depends(get_db)
):
    news_list, total = await NewsCRUD.get_news(db, category_id, (page - 1) * pagesize, pagesize)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": news_list,
            "total": total,
            "hasMore": total > (page - 1) * pagesize + pagesize
        }
    }
