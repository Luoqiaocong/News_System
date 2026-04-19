
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from Config.settings import get_db
from Schemas.Users import UserRequest
from CRUD import UsersCRUD

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/user")
async def register(userdata: UserRequest, db: AsyncSession = Depends(get_db)):
    existing_user = await UsersCRUD.search_user(db, userdata.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = await UsersCRUD.create_user(db, userdata)

    return {
        "code": 200,
        "msg": "registered",
        "data": {
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "token": user.token,
            "bio": user.bio
        }
    }
