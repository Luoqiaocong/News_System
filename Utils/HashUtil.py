from fastapi import HTTPException
from hashids import Hashids

from Config.settings import settings

hashids = Hashids(salt=settings.HASH_SALT, min_length=12)

def get_hashed_id(real_id: int) -> str:
    return hashids.encode(real_id)

def get_real_id(hashed_id: str) -> int:
    decoded = hashids.decode(hashed_id)
    if not decoded:
        raise HTTPException(status_code=400, detail="登录异常，请重新登录")
    return decoded[0]
