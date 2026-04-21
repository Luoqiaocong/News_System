from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from Config.settings import get_db
from Schemas.UsersSchema import UserInfo, UserRequest,UserAuthResponse
from CRUD import UsersCRUD
from Utils.response import success_response

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register")
async def register(userdata: UserRequest, db: AsyncSession = Depends(get_db)):
    existing_user = await UsersCRUD.search_user(db, userdata)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = await UsersCRUD.create_user(db, userdata)
    token = await UsersCRUD.create_token(db, user.id)

    account_info = UserAuthResponse(token=token,userInfo=UserInfo.model_validate(user))

    return success_response(message="注册成功", data=account_info)


@router.post("/login")
async def login(userdata: UserRequest, db: AsyncSession = Depends(get_db)):
    user = await UsersCRUD.verify_user(db, userdata)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或者密码错误！")


    account_info = UserAuthResponse(userInfo=UserInfo.model_validate(user))

    return success_response(message="登录成功", data=account_info)
