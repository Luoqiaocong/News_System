from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query
from fastapi.params import Body
from starlette import status
from fastapi_utils.cbv import cbv
from Dependency import JWTAuth
from Route.UnifiedRoute import UnifiedRoute
from models.User import User
from Service import UserFavService

router = APIRouter(prefix="/api/user/news/fav", tags=["用户收藏"],route_class=UnifiedRoute)

@cbv(router)
class UserFavRouterAPI:

    service: UserFavService = Depends()
    current_user: User = Depends(JWTAuth.get_current_user)

    @router.post("/{news_id}", status_code=status.HTTP_201_CREATED, summary="添加收藏")
    async def add(
        self,
        news_id: Annotated[int, Path(ge=1, description="新闻ID")]
    ):
        await self.service.add_favorite(news_id, self.current_user.id)

    @router.delete("/delete", status_code=status.HTTP_200_OK, summary="取消收藏")  # 删除收藏
    async def remove(
        self,
        news_ids: Annotated[list[int], Body(embed=True, min_length=1, description="新闻ID列表")],
    ):
        counts = await self.service.remove_favorites(news_ids, self.current_user.id)
        return {"deleted_counts": counts}

    @router.get("/check/{news_id}", summary="检查新闻是否收藏", status_code=status.HTTP_200_OK)
    async def check(
        self,
        news_id: Annotated[int, Path(ge=1)],
    ):
        is_fav = await self.service.check_favorite(news_id, self.current_user.id)
        return {"is_fav": is_fav}

    @router.get("/", summary="获取当前用户所有收藏", status_code=status.HTTP_200_OK)
    async def get(
        self,
        page: Annotated[int, Query(ge=1, description="页码")] = 1,
        page_size: Annotated[int, Query(ge=1, le=50, description="返回数据个数", alias="pagesize")] = 10,
    ):
        return await self.service.get_favorites(self.current_user.id, page, page_size)

    @router.delete("/", status_code=status.HTTP_200_OK, summary="清空当前用户所有收藏")
    async def clear(self):
        counts = await self.service.clear_favorites(self.current_user.id)
        return {"deleted_counts":counts}  
