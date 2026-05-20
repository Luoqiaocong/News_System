import re

from Exception import UserException, ResponseCode


def verify_password(cur_pwd: str, user):
    if cur_pwd != user.password:
        raise UserException(code=ResponseCode.USER_PWD_AUTH_FAILED)


def validate_password_strength(password: str):
    if len(password) < 8:
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[a-z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[A-Z]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
    if not re.search(r'[0-9]', password):
        raise UserException(code=ResponseCode.USER_PWD_WEAK)
