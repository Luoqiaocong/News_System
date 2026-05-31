from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi_utils.cbv import cbv
from starlette import status

from Dependency import JWTAuth
from Route.UnifiedRoute import UnifiedRoute
from Schemas.UserSchema import LogoutRequest, UserInfo,UserPwdAuth, RegisterUserRequest, \
    LoginUserRequest, UserPwdResetAuth
from Service import UserService
from models.User import User

router = APIRouter(prefix="/api/user", tags=["用户行为"], route_class=UnifiedRoute)


@cbv(router)
class UserPublicAPI:
    service: UserService = Depends()

    @router.post("/reg", summary="用户注册", status_code=status.HTTP_201_CREATED)
    async def register(self, userdata: RegisterUserRequest):
        await self.service.create_user(userdata)

    @router.post("/login", summary="用户登录", status_code=status.HTTP_200_OK)
    async def login(self, userdata: LoginUserRequest):
        token = await self.service.login_user(userdata)
        return token

    @router.post("/resetpwd", summary="重置密码", status_code=status.HTTP_200_OK)
    async def reset_pwd(self, user_request: UserPwdResetAuth):
        await self.service.reset_user_password(user_request)


@cbv(router)
class UserPrivateAPI:
    service: UserService = Depends()
    current_user: User = Depends(JWTAuth.get_current_user)

    @router.delete("/delete", summary="注销账户", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_account(self):
        await self.service.delete_user(self.current_user.email)

    @router.get("/info", summary="获取用户信息", status_code=status.HTTP_200_OK)
    async def get_user_info(self):
        return UserInfo.model_validate(self.current_user)

    @router.put("/update", summary="更新用户信息", status_code=status.HTTP_200_OK)
    async def update_user_info(
            self,
            nickname: Annotated[str | None, Form(max_length=10)] = None,
            bio: Annotated[str | None, Form(max_length=100)] = None,
            avatar_file: Annotated[UploadFile | None, File()] = None
    ):
        return await self.service.update_user({
            "email": self.current_user.email,
            "nickname": nickname,
            "bio": bio,
            "avatar": [avatar_file, self.current_user.avatar]
        })

    @router.put("/updatepwd", summary="更新密码", status_code=status.HTTP_200_OK)
    async def update_pwd(self, pwd_data: UserPwdAuth): # 更新密码
        await self.service.update_user_password(pwd_data, self.current_user)


    @router.post("/logout", status_code=status.HTTP_200_OK,summary="用户登出")
    async def logout_endpoint(self,
    payload: LogoutRequest, 
):
        await self.service.logout_user(self.current_user.id, payload.refresh_token)
       
