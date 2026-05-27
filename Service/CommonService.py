import asyncio
import random
import string

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