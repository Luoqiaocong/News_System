from typing import Annotated

from fastapi import APIRouter, Path, Depends, Query, Body
from fastapi_utils.cbv import cbv
from starlette import status

from Dependency import JWTAuth
from Route.UnifiedRoute import UnifiedRoute
from Schemas.UserSchema import UserInfo
from Service import UserHistService

router = APIRouter(prefix="/api/user/news/hist", tags=["用户浏览历史"],route_class=UnifiedRoute)


@cbv(router)
class UserHistRouter:
    service: UserHistService = Depends()
    current_user: UserInfo = Depends(JWTAuth.get_current_user)


    @router.delete("/delete", summary="删除浏览历史", status_code=status.HTTP_200_OK)
    async def delete(
            self,
            news_ids: Annotated[list[int], Body(embed=True, description="新闻ID列表", min_length=1)],
    ):
        count = await self.service.delete_hists(self.current_user.id, news_ids)
        return {"deleted_count": count}
    

    @router.get("/", summary="获取浏览历史", status_code=status.HTTP_200_OK)
    async def get(
            self,
            page: Annotated[int, Query(ge=1, description="页码", alias="page")],
            page_size: Annotated[int, Query(ge=1, description="每页数量", alias="pagesize")]=6,
    ):
        return await self.service.get_hists(self.current_user.id, page, page_size)

    @router.delete("/", summary="清空浏览历史", status_code=status.HTTP_200_OK)
    async def clear(
            self,
    ):
        count = await self.service.clear_hists(self.current_user.id)
        return {"deleted_count": count}
