from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import close_pool, init_pool
from routers import admin, export, manage, pages
from config import settings
from database import close_pool, get_pool, init_pool, run_migrations
from routers import export, pages
from routers.auth import AuthMiddleware, router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await run_migrations(get_pool())
    yield
    await close_pool()


app = FastAPI(title="PierceGate Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

# SessionMiddleware must be added last so it wraps AuthMiddleware (runs first on requests)
app.add_middleware(AuthMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(auth_router)
app.include_router(pages.router)
app.include_router(manage.router, prefix="/manage")
app.include_router(admin.router, prefix="/admin")
app.include_router(export.router, prefix="/export")


@app.get("/health")
async def health():
    return {"status": "ok"}
