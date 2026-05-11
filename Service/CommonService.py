from fastapi import HTTPException
from starlette import status

from Exception import ResponseCode
from Utils.RedisUtil import redis_client
from Utils.EmailUtil import EmailHelper
from Utils.ResponseUtil import success_response


class CommonService:

    @staticmethod
    async def send_code(email):
        code = await EmailHelper.send_code(email)
        if not code:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="服务器开小差了，请稍后再试")
        await redis_client.set(key=f"user:verifyCode:{email}",value=code,expire=180)