import asyncio
import random
import string

from Exception import ResponseCode
from Exception.BusinessException import AuthException
from Utils.AuthUtil import create_access_token
from Utils.HashUtil import get_real_id
from Schemas.CommonSchema import RefreshRequest
from Utils.LogUtil import log
from Utils.RedisUtil import redis_client
from Utils.EmailUtil import EmailHelper


class CommonService:

    @staticmethod
    async def send_code(email: str):
        # 1. 生成验证码，立即存入 Redis（确保即使邮件发送失败用户也能收到）
        code = ''.join(random.choices(string.digits, k=6))
        await redis_client.set(key=f"user:verifyCode:{email}", value=code, expire=180)

        # 2. 后台发送邮件，不阻塞响应
        asyncio.create_task(CommonService._do_send_email(email, code))

        log.info(f"验证码已生成并存储，key: user:verifyCode:{email}")

    @staticmethod
    async def _do_send_email(email: str, code: str):
        try:
            success = await EmailHelper.send_code(email, code)
            if success:
                log.info(f"后台邮件发送成功: {email}")
            else:
                log.error(f"后台邮件发送失败: {email}")
        except Exception as e:
            log.error(f"后台邮件发送异常: {email}, error: {e}")


    @staticmethod
    async def refresh_token_endpoint(payload: RefreshRequest):
        user_id_hashed = payload.user_id
        user_id = get_real_id(user_id_hashed)
        refresh_token = payload.refresh_token

        redis_list_key = f"user:refresh_tokens:{user_id}"
        blacklist_key = f"token:blacklist:{refresh_token}"

        # 1. 安全防御 A：去黑名单看看这个 Token 是不是已经被别的设备挤下线了
        is_kicked = await redis_client.get(blacklist_key)
        if is_kicked:
            raise AuthException(
                code=ResponseCode.TOKEN_EXPIRED,
                msg="会话已过期，请重新登录"
            )

        # 2. 安全防御 B：去用户的活跃列表中查看，确保它还在前三名里
        active_tokens = await redis_client.lrange(redis_list_key, 0, -1)
        if refresh_token not in active_tokens:
            raise AuthException(
                code=ResponseCode.TOKEN_EXPIRED,
                msg="会话已过期，请重新登录"
            )

        # 3. 双层验证通过！现场印制一颗全新的、寿命极短的 AccessToken 丢回去
        new_access_token = create_access_token(data={"sub": user_id_hashed})

        return {"access_token": new_access_token}
    