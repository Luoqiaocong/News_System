from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi_utils.cbv import cbv
from starlette import status

from Dependency import JWTAuth
from Route.UnifiedRoute import UnifiedRoute
from Schemas.UserSchema import UserInfo, UserToken, UserPwdAuth, RegisterUserRequest, \
    LoginUserRequest, UserPwdResetAuth
from Service import UserService
from Utils.ResponseUtil import success_response
from models.User import User

router = APIRouter(prefix="/api/user", tags=["用户行为"], route_class=UnifiedRoute)  # router_class 还没学习


# ==============================================
# @cbv(router) 是 FastAPI 的类视图增强装饰器
# 1. 这是 类属性级别 的依赖注入
# 2. 在普通 Python 类里，这样写会直接报错
# 3. 但在 @cbv 装饰后，CBV 会在 创建当前类实例的时候自动帮你把 Depends() 解析并赋值给这个类属性
# 4. 每一次都是新的依赖实例
# ==============================================
@cbv(router)
class UserPublicAPI:  # 无需token鉴权接口类
    service: UserService = Depends()

    @router.post("/reg", summary="用户注册", status_code=status.HTTP_201_CREATED)
    async def register(self, userdata: RegisterUserRequest):
        # 只创建用户，不生成token
        await self.service.create_user(userdata)

    @router.post("/login", summary="用户登录", status_code=status.HTTP_200_OK)
    async def login(self, userdata: LoginUserRequest):
        # 每次登录生成新token（包括注册后第一次登录），这样实现了多点登录
        '''
        单点登录？多点登录？
        '''
        token = await self.service.login_user(userdata)
        return UserToken(token=token)

    @router.post("/resetpwd", summary="重置密码", status_code=status.HTTP_200_OK)
    async def reset_pwd(
            self,
            user_request: UserPwdResetAuth,
    ):
        await self.service.reset_user_password(user_request)


@cbv(router)
class UserPrivateAPI:  # 需token鉴权接口类

    service: UserService = Depends()
    current_user: User = Depends(JWTAuth.get_current_user)

    @router.delete("/delete", summary="注销账户", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_account(self):
        await self.service.delete_user(self.current_user.email)

    @router.get("/info", summary="获取用户信息", status_code=status.HTTP_200_OK)
    async def get_user_info(self):
        return UserInfo.model_validate(self.current_user)  # UserInfo过滤一些敏感字段

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
    async def update_pwd(
            self,
            pwd_data: UserPwdAuth,
    ):
        await self.service.update_user_password(pwd_data, self.current_user)
