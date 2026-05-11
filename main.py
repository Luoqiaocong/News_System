from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from Dependency.register_exception import register_exception
from MIddleware import PerformanceMiddleware,UnifiedResponseMiddleware
from Router import NewsRouter, UserRouter, UserFavoriteRouter, UserHistoryRouter, CommonRouter
from Test.fileTest import router as test_router
from Utils.LogUtil import init_log
from Utils.RedisUtil import redis_client
from models import * # 确保所有模型都被导入过




@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：建立连接
    await redis_client.init_redis()
    yield
    # 关闭时：释放连接
    await redis_client.close()
app = FastAPI(lifespan=lifespan)

# 注册路由
app.include_router(NewsRouter.router)
app.include_router(UserRouter.router)
app.include_router(UserFavoriteRouter.router)
app.include_router(UserHistoryRouter.router)
app.include_router(CommonRouter.router)
app.include_router(test_router)

# 注册异常
register_exception(app)

# 注册中间件
# app.add_middleware(UnifiedResponseMiddleware)
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

