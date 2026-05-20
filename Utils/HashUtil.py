from fastapi import HTTPException
from hashids import Hashids
import secrets

from Config.settings import settings

hashids = Hashids(salt=settings.HASH_SALT, min_length=12)

def get_hashed_id(real_id: int) -> str:
    return hashids.encode(real_id)

def get_real_id(hashed_id: str) -> int:
    decoded = hashids.decode(hashed_id)
    if not decoded:
        raise HTTPException(status_code=400, detail="无效的 ID 格式")
    return decoded[0]

def create_refresh_token_urlsafe() -> str:
    return secrets.token_urlsafe(64)

def create_refresh_token_hex() -> str:
    return secrets.token_hex(32)
