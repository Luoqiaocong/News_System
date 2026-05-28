import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from Exception import UserException, ResponseCode


class PasswordManager:
    _ph = PasswordHasher()

    @classmethod
    def hash(cls, password: str) -> str:
        return cls._ph.hash(password)

    @classmethod
    def verify(cls, plain_password: str, hashed_password: str) -> bool:
        try:
            return cls._ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False


def validate_password_strength(password: str):
    if len(password) < 8:
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[a-z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[A-Z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[0-9]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
