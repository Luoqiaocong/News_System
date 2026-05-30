from datetime import timedelta, datetime, timezone
import hashlib
import secrets
from typing import Optional

from jose import jwt

from Config.settings import settings
from Utils.RedisUtil import redis_client

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    """生成长寿命、高强度的全球唯一随机字符串作为 RefreshToken"""
    # 生成 32 字节的十六进制安全随机数（比普通的 UUID 更加防猜测、防碰撞）
    return secrets.token_hex(32)



async def _manage_device_slots(user_id: int, refresh_token: str):
    """将 RefreshToken 的 MD5 登记进 Redis 列表，严格控死最多 3 个设备"""
    # 计算 MD5，防止 Redis 里存超长明文浪费内存
    rt_md5 = hashlib.md5(refresh_token.encode()).hexdigest()
    
    redis_list_key = f"user:refresh_tokens:{user_id}"
    blacklist_prefix = "token:blacklist:"
    
    # 整个活跃列表的生命周期（秒数）
    list_ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    # 黑名单墓碑的生命周期（秒数）：AccessToken 最大寿命 15 分钟 + 5 分钟网络缓冲
    safe_blacklist_ttl = (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60) + 300

    # 1. 开启第一个 Redis 异步管道，打包处理活跃设备槽
    async with redis_client.pipeline() as pipe:
        # a. 把最新的这个 RefreshToken 压进队列最左侧（头部）
        pipe.lpush(redis_list_key, rt_md5)
        
        # b. 必须在 LTRIM 剪裁之前，先去捞出索引 3 往后的所有老 Token 记录！
        # 此时新 Token 已经进去了，如果原本有 3 个，现在就是 4 个，索引 3 就是最老的那颗
        pipe.lrange(redis_list_key, 3, -1)
        
        # c. 记录完后，再举起大刀严格裁剪队列，只保留索引 0, 1, 2
        pipe.ltrim(redis_list_key, 0, 2)
        
        # d. 顺手把整个活跃设备列表的 7 天寿命给刷新了（打包进管道，节省一次网络开销）
        pipe.expire(redis_list_key, list_ttl_seconds)
        
        # 2. 一次性发射执行
        # 注意：execute() 返回的是一个数组，按上面 pipe 写的顺序依次对应：
        # results[0] -> lpush 的结果 (列表新长度)
        # results[1] -> lrange 的结果 (捞出来的 kicked_tokens 数组)
        # results[2] -> ltrim 的结果 (OK)
        # results[3] -> expire 的结果 (True/False)
        results = await pipe.execute()
        kicked_tokens = results[1] # 成功拿到被裁剪掉的老 Token 标识
        
    # 3. 如果发现确实有老设备被无情挤退了，开启第二个管道，送它们上黑名单
    if kicked_tokens:
        async with redis_client.pipeline() as pipe:
            for old_rt_md5 in kicked_tokens:
                # 扔进黑名单，20分钟（1200秒）后全自动物理蒸发，绝不白白占用 Redis 内存
                pipe.setex(f"{blacklist_prefix}{old_rt_md5}", safe_blacklist_ttl, "kicked")
            await pipe.execute()