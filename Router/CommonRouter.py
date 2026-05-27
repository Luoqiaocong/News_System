
from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from starlette import status

from Route.UnifiedRoute import UnifiedRoute
from Schemas.CommonSchema import VerifyEmail
from Service.CommonService import CommonService

router = APIRouter(prefix="/api/common",tags=['通用接口'], route_class=UnifiedRoute)

@cbv(router)
class CommonRouterAPI:

    service: CommonService = Depends()

    @router.post('/sendCode',status_code=status.HTTP_200_OK)
    async def send_code(self,email:VerifyEmail):
        await self.service.send_code(email.email)


