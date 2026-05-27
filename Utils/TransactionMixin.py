from contextlib import asynccontextmanager

from Exception import ResponseCode
from Exception.BusinessException import BaseBusinessException
from Utils.LogUtil import log


class TransactionMixin:
    _business_exception_type: type[BaseBusinessException] = BaseBusinessException

    @asynccontextmanager
    async def transaction_scope(self):
        try:
            yield
            await self.db.commit()  # type: ignore
        except self._business_exception_type:
            await self.db.rollback()  # type: ignore
            raise
        except Exception as e:
            log.error(f"未捕获的系统异常: {e}")
            await self.db.rollback()  # type: ignore
            raise BaseBusinessException(code=ResponseCode.DATABASE_ERROR)
