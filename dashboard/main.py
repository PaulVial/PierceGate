from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import close_pool, init_pool
from routers import admin, export, manage, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="PierceGate Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(manage.router, prefix="/manage")
app.include_router(admin.router, prefix="/admin")
app.include_router(export.router, prefix="/export")


@app.get("/health")
async def health():
    return {"status": "ok"}
