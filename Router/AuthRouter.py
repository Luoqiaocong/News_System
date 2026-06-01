
import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from starlette import status

from Route.UnifiedRoute import UnifiedRoute
from Schemas.CommonSchema import RefreshRequest, VerifyEmail
from Service import AuthService

router = APIRouter(prefix="/api/auth",tags=['通用接口'], route_class=UnifiedRoute)

@cbv(router)
class AuthRouterAPI:

    service: AuthService = Depends()

    @router.post('/sendCode',status_code=status.HTTP_200_OK)
    async def send_code(self,email:VerifyEmail):
        await self.service.send_code(email.email)


    @router.post("/refresh")
    async def refresh_token_endpoint(self,payload: RefreshRequest):
        return await self.service.refresh_token_endpoint(payload)
       


