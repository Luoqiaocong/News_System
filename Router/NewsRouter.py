# Router/NewsRouter.py
from typing import Annotated,  Optional
from fastapi import Query, Path
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
            category_id: Annotated[Optional[int], Query(ge=1, description="新闻类型id")] = None, # 可以不传，传了就得大于0
    ):
        return await self.service.get_news_categories(category_id)


    @router.get("/list",summary="获取新闻数据")
    async def get_news(self,
            category_id: Annotated[int,Query(ge=1,description="新闻类型ID", alias="categoryId")]=None,
            page: int = 1,
            page_size: int = Query(10, lt=50, description="每页新闻数量", alias="pagesize"),
    ):
        return await self.service.get_news_list(category_id,page,page_size)


    @router.get("/detail/{news_id}", summary="查看新闻详情")
    async def get_news_detail(self,
            news_id: int = Path(..., description="新闻ID"),
    ):
        return await self.service.get_news_detail(news_id) # 获取新闻详情及相关推荐新闻
        await self.service.handle_news_view(news_id, self.current_user)   # 处理浏览量和浏览历史
        pass
        # news_detail = await NewsRepo.get_news_detail(db, news_id)
        #
        # related_news = await NewsRepo.get_related_news(db, news_id, news_detail.category_id)
        #
        # detail_data = NewsData.model_validate(news_detail)
        # related_data = [NewsData.model_validate(news) for news in related_news]
        #
        # await NewsService.handle_news_view(db, news_id, user)   # 处理浏览量和浏览历史
        #
        # return success_response(data={"detail": detail_data, "related_news": related_data})

