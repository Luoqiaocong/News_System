# Router/NewsRouter.py
from typing import Annotated,  Optional
from fastapi import BackgroundTasks, Query, Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from Dependency import JWTAuth
from Route.UnifiedRoute import UnifiedRoute
from Schemas.NewsSchema import CategoryData, NewsData
from Repo import NewsRepo
from Config.DataBaseConfig import get_db
from Schemas.UserSchema import UserInfo
from Service import NewsService
from Utils.ResponseUtil import success_response

router = APIRouter(prefix="/api/news", tags=["新闻相关"],route_class=UnifiedRoute)

@cbv(router)
class NewsRouterAPI:
    service :NewsService = Depends()
    current_user :UserInfo = Depends(JWTAuth.get_current_user_optional)

    @router.get("/categories",summary="获取新闻分类")
    async def get_categories(self,
            category_id: Annotated[int, Query(ge=1, description="新闻类型id",alias="categoryId")] = None, # 可以不传，传了就得大于0
    ):
        return await self.service.get_news_categories(category_id)


    @router.get("/list",summary="获取新闻数据")
    async def get_news(self,
            category_id: Annotated[int, Query(ge=1, description="新闻类型ID", alias="categoryId")]=None,
            page: Annotated[int, Query(ge=1, description="页码", alias="page")] = 1,
            page_size: Annotated[int, Query(ge=1, le=50, description="每页新闻数量", alias="pagesize")] = 10,
    ):
        return await self.service.get_news_list(category_id,page,page_size)


    @router.get("/detail/{news_id}", summary="查看新闻详情")
    async def get_news_detail(self,
            background_tasks: BackgroundTasks,
            news_id: int = Path(..., description="新闻ID"),
          
    ):
        result = await self.service.get_news_detail(news_id)
        background_tasks.add_task(self.service.handle_news_view, news_id, self.current_user)
        return success_response(data=result)
