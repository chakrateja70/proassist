from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse

from app.api.routes.auth import router as auth_router
from app.api.routes.drafts import router as drafts_router
from app.api.routes.history import router as history_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.me import router as me_router
from app.api.routes.profile import router as profile_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.sends import router as sends_router
from app.api.routes.worker import router as worker_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

settings = get_settings()
app = FastAPI(title=settings.app_name)


def build_allowed_origins(frontend_url: str) -> list[str]:
    origins = {frontend_url.rstrip("/")}
    parsed = urlparse(frontend_url)
    if parsed.scheme and parsed.netloc:
        host = parsed.hostname
        port = f":{parsed.port}" if parsed.port else ""
        if host == "localhost":
            origins.add(f"{parsed.scheme}://127.0.0.1{port}")
        elif host == "127.0.0.1":
            origins.add(f"{parsed.scheme}://localhost{port}")
    return sorted(origins)


app.add_middleware(
    CORSMiddleware,
    allow_origins=build_allowed_origins(settings.frontend_url),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(me_router)
app.include_router(profile_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(drafts_router)
app.include_router(sends_router)
app.include_router(history_router)
app.include_router(worker_router)
