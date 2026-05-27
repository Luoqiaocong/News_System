import re
import asyncio
import bcrypt

from Exception import UserException, ResponseCode


class AsyncPasswordManager:
    def __init__(self, rounds: int = 10):
        self._rounds = rounds

    async def hash(self, password: str) -> str:
        def _hash():
            return bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt(self._rounds)
            )
        return (await asyncio.to_thread(_hash)).decode('utf-8')

    async def verify(self, plain: str, hashed: str) -> bool:
        def _verify():
            return bcrypt.checkpw(plain.encode('utf-8')[:72], hashed.encode('utf-8'))
        return await asyncio.to_thread(_verify)


pwd_manager = AsyncPasswordManager()


def validate_password_strength(password: str):
    if len(password) < 8:
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[a-z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[A-Z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[0-9]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
