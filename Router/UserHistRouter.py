
from typing import Annotated

from fastapi import APIRouter, Path, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from Config.DataBaseConfig import get_db
from Dependency import JWTAuth
from Repo import UserHistRepo
from Schemas.UserHistSchema import UserHistResponse
from Schemas.UserSchema import UserInfo
from Utils.LogUtil import log
from Utils.ResponseUtil import success_response

router = APIRouter(prefix="/api/user/news/hist",tags=["用户浏览历史"])


@router.get("/{news_id}",summary="添加浏览历史",deprecated=True)
async def add(
        news_id: Annotated[int, Path(ge=1, description="新闻ID")],
        user: Annotated[UserInfo, Depends(JWTAuth.get_current_user)],
        db: AsyncSession = Depends(get_db),
):
    pass

@router.delete("/delete", summary="删除浏览历史",status_code=status.HTTP_200_OK)
async def delete(
        news_ids: Annotated[list[int], Body(embed=True, description="新闻ID列表", min_length=1)], # 直接在请求体中提取news_ids字段
        user: Annotated[UserInfo, Depends(JWTAuth.get_current_user)],
        db: AsyncSession = Depends(get_db),
):
    log.info(f"用户 '{user.email}' 删除了浏览历史")
    count = await UserHistRepo.delete_history(user.id, news_ids, db)
    return success_response(message=f"操作成功，删除了{count}条浏览记录")



@router.get("/",summary="获取浏览历史",status_code=status.HTTP_200_OK)
async def get(
        user: Annotated[UserInfo, Depends(JWTAuth.get_current_user)],
        page: Annotated[int, Query(ge=1, description="页码", alias="page")],
        page_size: Annotated[int, Query(ge=1, description="每页数量", alias="pagesize")],
        db: AsyncSession = Depends(get_db),
):
    rows,total =  await UserHistRepo.get_all_history(user.id, page, page_size, db)
    hist_lt = [
        {
            **news.__dict__,
            "viewed_at": viewed_at,
            "history_id": history_id
        }
        for news, viewed_at, history_id in rows
    ]
    data = UserHistResponse(hist_lt=hist_lt, total=total)
    return success_response(message="获取浏览历史成功",data=data)


@router.delete("/", summary="清空浏览历史", status_code=status.HTTP_200_OK)
async def clear(
        user: Annotated[UserInfo, Depends(JWTAuth.get_current_user)],
        db: AsyncSession = Depends(get_db),
):
    log.info(f"用户 '{user.email}' 清空了浏览历史")
    count = await UserHistRepo.remove_all(user.id, db)
    return success_response(message=f"删除了{count}条记录")
