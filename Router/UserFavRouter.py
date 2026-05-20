from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query
from fastapi.params import Body
from starlette import status
from fastapi_utils.cbv import cbv
from Dependency import JWTAuth
from Schemas.UserFavSchema import UserFavResponse
from Schemas.UserSchema import UserInfo
from Service import UserFavService
from Utils.LogUtil import log
from Utils.ResponseUtil import success_response

router = APIRouter(prefix="/api/user/news/fav", tags=["用户收藏"])

@cbv(router)
class UserFavRouter():

    service: UserFavService = Depends()
    current_user: UserInfo = Depends(JWTAuth.get_current_user)

    @router.post("/{news_id}", status_code=status.HTTP_201_CREATED, summary="添加收藏")
    async def add(
        self,
        news_id: Annotated[int, Path(ge=1, description="新闻ID")]
    ):
        await self.service.add_favorite(news_id, self.current_user.id)

    @router.delete("/delete", status_code=status.HTTP_200_OK, summary="取消收藏")
    async def remove(
        self,
        news_ids: Annotated[list[int], Body(embed=True, min_length=1, description="新闻ID列表")],
    ):
        log.info(f"用户 '{self.current_user.email}' 取消收藏 '{news_ids}'")
        count = await self.service.remove_favorites(news_ids, self.current_user.id)
        return success_response(message=f"取消收藏成功，共取消{count}条记录")

    @router.get("/check/{news_id}", summary="检查新闻是否收藏", status_code=status.HTTP_200_OK)
    async def check(
        self,
        news_id: Annotated[int, Path(ge=1)],
    ):
        is_fav = await self.service.check_favorite(news_id, self.current_user.id)
        return success_response(data={"is_fav": is_fav})

    @router.get("/", summary="获取当前用户所有收藏", status_code=status.HTTP_200_OK)
    async def get(
        self,
        page: Annotated[int, Query(ge=1, description="页码")] = 1,
        page_size: Annotated[int, Query(ge=1, le=50, description="返回数据个数", alias="pagesize")] = 10,
    ):
        rows, total = await self.service.get_favorites(self.current_user.id, page, page_size)
        fav_lt = [{
            **news.__dict__,
            "favorited_at": favorited_at,
            "favorite_id": favorite_id
        } for news, favorited_at, favorite_id in rows]
        data = UserFavResponse(fav_lt=fav_lt, total=total)
        return success_response(message="获取新闻收藏列表成功", data=data)

    @router.delete("/", status_code=status.HTTP_200_OK, summary="清空当前用户所有收藏")
    async def clear(self):
        log.info(f"用户 '{self.current_user.email}' 清空收藏")
        res = await self.service.clear_favorites(self.current_user.id)
        return success_response(message=f"删除了{res}条记录")
