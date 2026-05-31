from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Config.DataBaseConfig import get_db
from Exception.BusinessException import UserHistException
from Repo.UserHistRepo import UserHistRepo
from Schemas.UserHistSchema import HistoryNewsItem, UserHistResponse
from Utils.ServiceDecorator import HandlerServiceException
from Utils.TransactionMixin import TransactionMixin
from Utils.SchemaUtil import rows_to_schema

@HandlerServiceException
class UserHistService(TransactionMixin):
    _business_exception_type = UserHistException

    def __init__(self, repo: Annotated[UserHistRepo, Depends()]
                 , db: Annotated[AsyncSession, Depends(get_db)]):
        self.repo = repo
        self.db = db

    async def delete_hists(self, user_id: int, news_ids: list[int]) -> int:
        if not news_ids:
            return 0
        async with self.transaction_scope():
            return await self.repo.delete(user_id, news_ids)

    async def get_hists(self, user_id: int, page: int, page_size: int):
        rows, total = await self.repo.get(user_id, page, page_size)
        items = rows_to_schema(HistoryNewsItem, rows, ("viewed_at", "history_id"))
        return UserHistResponse(hist_lt=items, total=total)

    async def clear_hists(self, user_id: int) -> int:
        async with self.transaction_scope():
            return await self.repo.remove(user_id)