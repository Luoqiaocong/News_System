from fastapi import HTTPException
from starlette import status
from Utils.LogUtil import log
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
        log.info(f"验证码已存储在 Redis，key: user:verifyCode:{email}, value: {code}")