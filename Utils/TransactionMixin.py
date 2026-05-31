from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

from Exception import ResponseCode
from Exception.BusinessException import BaseBusinessException
from Utils.LogUtil import log


class TransactionMixin:
    _business_exception_type: type[BaseBusinessException] = BaseBusinessException
    db: AsyncSession

    @asynccontextmanager
    async def transaction_scope(self):
        try:
            yield
            await self.db.commit()
        except Exception:  # 这里使用Exception捕获所有异常，回滚然后抛给service类异常处理
            await self.db.rollback()
            raise
'''
套上这个装饰器会给整个函数加上事务控制，不利于一些不操作数据库的service方法，这种情况自己调用transaction_scope就好了
'''
def transactional(
    func: Callable[..., Coroutine[Any, Any, Any]]
) -> Callable[..., Coroutine[Any, Any, Any]]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        
        self_instance = args[0]
        
        async with self_instance.transaction_scope():
            return await func(*args, **kwargs)

    return wrapper