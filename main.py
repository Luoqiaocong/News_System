from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from Router import NewsRouter, UsersRouter
app = FastAPI()
app.include_router(NewsRouter.router)
app.include_router(UsersRouter.router)


# 允许跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，开发阶段很方便
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")
