from typing import Annotated
from fastapi import APIRouter, Depends, Path, HTTPException, Query
from fastapi.params import Body
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from fastapi_utils.cbv import cbv
from Repo import UserFavRepo
from Repo import UserFavRepo
from Config.DataBaseConfig import get_db
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

    # 1. 添加收藏
    @router.post("/{news_id}", status_code=status.HTTP_201_CREATED, summary="添加收藏")
    async def add(
        self,
        news_id: Annotated[int, Path(ge=1, description="新闻ID")]
    ):
        log.info(f"用户 '{self.current_user.email}' 添加收藏 '{news_id}'")
        await self.service.add_favorite(news_id, self.current_user.id)

    # 2. 取消收藏
    @router.delete("/delete", status_code=status.HTTP_200_OK, summary="取消收藏")
    async def remove(
        self,
        news_ids:Annotated[list[int],Body(embed=True,min_length=1, description="新闻ID列表")] , # 直接在请求体中提取news_ids字段
        db: AsyncSession = Depends(get_db),
    ):
        log.info(f"用户 '{user.email}' 取消收藏 '{news_ids}'")
        count = await remove_favorite(news_ids, user.id, db)
        return success_response(message=f"取消收藏成功，共取消{count}条记录")


    # 3. 检查新闻是否已收藏
    @router.get("/check/{news_id}", summary="检查新闻是否收藏",status_code=status.HTTP_200_OK)
    async def check(
        self,
        news_id: Annotated[int, Path(ge=1)],
        db: AsyncSession = Depends(get_db),
    ):
        is_fav = await UserFavRepo.check_is_favorite(news_id,user.id,db)
        return success_response(data={"is_fav":is_fav})

    # 4. 获取当前用户所有收藏
    @router.get("/", summary="获取当前用户所有收藏",status_code=status.HTTP_200_OK)
    async def get(
        self,
        page:Annotated[int,Query(ge=1,description="页码")]=1,
        page_size:Annotated[int,Query(ge=1,le=50,description="返回数据个数",alias="pagesize")]=10,
        db: AsyncSession = Depends(get_db),
    ):
        rows,total = await UserFavRepo.get_all_favorites(user.id,page,page_size,db)
        fav_lt = [{
            **news.__dict__,
            "favorited_at":favorited_at,
            "favorite_id":favorite_id
        }for news,favorited_at,favorite_id in rows]
        data= UserFavResponse(fav_lt=fav_lt,total=total)
        return success_response(message="获取新闻收藏列表成功",data=data)

    # 5. 清空当前用户所有收藏
    @router.delete("/", status_code=status.HTTP_200_OK, summary="清空当前用户所有收藏")
    async def clear(
        self,
        db: AsyncSession = Depends(get_db),
    ):
        log.info(f"用户 '{user.email}' 清空收藏")
        res = await UserFavRepo.remove_all(user.id,db)
        return success_response(message=f"删除了{res}条记录")
