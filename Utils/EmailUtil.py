# Utils/EmailUtil.py
from email.message import EmailMessage
import aiosmtplib

from Config.settings import settings
from Utils.LogUtil import log


class EmailHelper:

    @staticmethod
    async def send_code(receiver: str, code: str) -> bool:
        message = EmailMessage()
        message["From"] = settings.SENDER
        message["To"] = receiver
        message["Subject"] = "【Seven新闻】Verify Code"
        message.set_content(f"【Seven新闻】您的验证码是：{code}，用于新闻系统身份验证，3分钟内有效，请勿泄露和转发，如非本人操作，请忽略此邮件。")

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                username=settings.SENDER,
                password=settings.AUTH_CODE,
                use_tls=True,
            )
            log.info(f"验证码已发送至邮箱: {receiver}")
            return True
        except Exception as e:
            log.error(f"邮件发送失败: {str(e)}")
            return False