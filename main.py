from fastapi import FastAPI
from Router import NewsRouter
app = FastAPI()
app.include_router(NewsRouter.router)
@app.get("/")
def read_root():
    return {"Hello": "World"}
