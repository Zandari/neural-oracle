from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .router import router
from .dependencies import repository_dependency


@asynccontextmanager
async def lifespan(app: FastAPI):
    async for repository in repository_dependency():
        await repository.init_database()

    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/auth")
async def auth():
    return FileResponse("static/auth.html")


app.include_router(router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")