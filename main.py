from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from Dependency.register_exception import register_exception
from MIddleware import PerformanceMiddleware
from Router import AuthRouter, NewsRouter, UserRouter, UserFavRouter, UserHistRouter
from Tasks.CleanMode.CleanUser import start_expired_user_cleanup, stop_expired_user_cleanup
from Utils.LogUtil import init_log
from Utils.RedisUtil import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==================== 【1. 启动阶段：yield 之前】 ====================
    # 核心原则：按依赖顺序，从最底层基础设施开始往上起
    
    # 1.1 先把物理连接池打通
    await redis_client.init_redis()
    
    # 1.2 基础设施好了，立刻拉起定时任务清道夫（给它配置好时钟，它会在后台独立线程自己走）
    start_expired_user_cleanup()
    
    yield  # 此时 Uvicorn 握手成功，服务正常接客、收发 HTTP 请求。
    
    # ==================== 【2. 收尾阶段：yield 之后】 ====================
    # 核心原则：当按下 Ctrl+C 关闭服务时，代码才会击穿到这里！
    # 顺序要和上面完全相反（洋葱模型）：先停上层业务定时器，再物理断开底层连接池
    
    # 2.1 掐断定时任务（不让新的清洗任务在关闭过程中乱跑）
    stop_expired_user_cleanup()
    
    # 2.2 最后彻底物理摧毁 Redis 连接，释放端口
    await redis_client.close()

app = FastAPI(lifespan=lifespan)

# 注册路由
app.include_router(NewsRouter.router)
app.include_router(UserRouter.router)
app.include_router(UserFavRouter.router)
app.include_router(UserHistRouter.router)
app.include_router(AuthRouter.router)

register_exception(app)
app.add_middleware(PerformanceMiddleware)

app.mount("/static", StaticFiles(directory="frontend"), name="static")  # 静态资源路径映射


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

