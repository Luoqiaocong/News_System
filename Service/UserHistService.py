from contextlib import asynccontextmanager
from typing import Annotated
from Exception.ResponseCode import ResponseCode
from Utils.LogUtil import log
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Config.DataBaseConfig import get_db
from Exception.BusinessException import BaseBusinessException, UserHistException
from Repo.UserHistRepo import UserHistRepo
from Schemas.UserHistSchema import HistoryNewsItem, UserHistResponse


class UserHistService:
    def __init__(self, repo: Annotated[UserHistRepo, Depends()]
                 , db: Annotated[AsyncSession, Depends(get_db)]):
        self.repo = repo
        self.db = db


    @asynccontextmanager
    async def transaction_scope(self):
        try:
            yield  # 这里会执行 async with 块内部的代码
            await self.db.commit()
        except UserHistException:
            await self.db.rollback()
            raise
        except Exception as e:
            log.error(f"未捕获的系统异常: {e}")
            await self.db.rollback()
            raise BaseBusinessException(code=ResponseCode.DATABASE_ERROR)

    async def delete_hists(self, user_id: int, news_ids: list[int]) -> int:
        if not news_ids:
            return 0
        async with self.transaction_scope():
            return await self.repo.delete(user_id, news_ids)

    async def get_hists(self, user_id: int, page: int, page_size: int):
        rows, total = await self.repo.get(user_id, page, page_size)
        items =[
            HistoryNewsItem.model_validate({

            **{h.name: getattr(news_obj, h.name) for h in news_obj.__table__.columns},
            "viewed_at": viewed_at,
            "history_id": history_id
            }) 
            for news_obj, viewed_at, history_id in rows
        ]
       
        return UserHistResponse(hist_lt=items, total=total)

    async def clear_hists(self, user_id: int) -> int:
        async with self.transaction_scope():
            return await self.repo.remove(user_id)