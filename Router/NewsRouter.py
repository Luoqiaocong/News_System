# Router/NewsRouter.py
from typing import Annotated,  Optional
from fastapi import Query, Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from Dependency import JWTAuth
from Schemas.NewsSchema import CategoryData, NewsData
from Repo import NewsRepo
from Config.DataBaseConfig import get_db
from Schemas.UserSchema import UserInfo
from Service import NewsService
from Utils.ResponseUtil import success_response

router = APIRouter(prefix="/api/news", tags=["新闻相关"])


@router.get("/categories",summary="获取新闻分类")
async def get_categories(
        category_id: Annotated[Optional[int], Query(ge=1, description="新闻类型id")] = None, # 可以不传，传了就得大于0
        db: AsyncSession = Depends(get_db)
):
    result = await NewsRepo.get_categories(category_id, db)
    # 手动转换 ORM 对象
    categories = [CategoryData.model_validate(cat) for cat in result]
    return success_response(data=categories)


@router.get("/list",summary="获取新闻数据")
async def get_news(
        category_id: int = Query(..., description="新闻类型ID", alias="categoryId"),
        page: int = 1,
        page_size: int = Query(10, lt=50, description="每页新闻数量", alias="pagesize"),
        db: AsyncSession = Depends(get_db)
):
    news_list, total = await NewsRepo.get_news(db, category_id, (page - 1) * page_size, page_size)

    # 手动转换 ORM 对象
    news_data = [NewsData.model_validate(news) for news in news_list]
    return success_response(data={"news_list": news_data, "total": total})


@router.get("/detail/{news_id}", summary="查看新闻详情")
async def get_news_detail(
        user: Annotated[UserInfo, Depends(JWTAuth.get_current_user_optional)], # 确认用户是否登录，登录了才会有浏览历史
        news_id: int = Path(..., description="新闻ID"),
        db: AsyncSession = Depends(get_db),
):
    news_detail = await NewsRepo.get_news_detail(db, news_id)

    related_news = await NewsRepo.get_related_news(db, news_id, news_detail.category_id)

    detail_data = NewsData.model_validate(news_detail)
    related_data = [NewsData.model_validate(news) for news in related_news]

    await NewsService.handle_news_view(db, news_id, user)   # 处理浏览量和浏览历史

    return success_response(data={"detail": detail_data, "related_news": related_data})

