from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from Dependency.register_exception import register_exception
from MIddleware import PerformanceMiddleware
from Router import NewsRouter, UserRouter, UserFavRouter, UserHistRouter, CommonRouter
from Utils.LogUtil import init_log
from Utils.RedisUtil import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 建立 Redis 连接
    await redis_client.init_redis()

    yield
    await redis_client.close()
app = FastAPI(lifespan=lifespan)

# 注册路由
app.include_router(NewsRouter.router)
app.include_router(UserRouter.router)
app.include_router(UserFavRouter.router)
app.include_router(UserHistRouter.router)
app.include_router(CommonRouter.router)

register_exception(app)
app.add_middleware(PerformanceMiddleware)


# 允许跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，开发阶段很方便
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"], # 允许所有方法
    allow_headers=["*"], # 允许所有请求头
)
# 初始化日志
init_log()
@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

