"""
ReadyDay API — FastAPI entry point
Dev:  uvicorn main:app --reload --port 8001
Prod: Docker + Caddy reverse proxy en /readyday
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import get_settings
from database import init_db
from scheduler import start_scheduler

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

# Rate limiter global (IP-based)
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(
    title="ReadyDay API",
    description="Score engine multi-wearable para readiness diario.",
    version="alpha1",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from routers import auth, snapshots, scores, devices, notifications, garmin  # noqa
app.include_router(auth.router)
app.include_router(snapshots.router)
app.include_router(scores.router)
app.include_router(devices.router)
app.include_router(notifications.router)
app.include_router(garmin.router)


# Health check (sin auth)
@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "readyday-api", "version": "alpha1"}


# Servir el frontend web desde /frontend
_FRONTEND = Path(__file__).parent.parent / "frontend"
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_landing():
        landing = _FRONTEND / "landing.html"
        if landing.exists():
            return FileResponse(str(landing))
        return FileResponse(str(_FRONTEND / "index.html"))

    @app.get("/app", include_in_schema=False)
    @app.get("/app/", include_in_schema=False)
    @app.get("/app/{path:path}", include_in_schema=False)
    def serve_app(path: str = ""):
        return FileResponse(str(_FRONTEND / "index.html"))

    @app.get("/{path:path}", include_in_schema=False)
    def serve_static_fallback(path: str = ""):
        # Archivos estáticos con extensión se sirven directamente
        file = _FRONTEND / path
        if file.exists() and file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(_FRONTEND / "index.html"))
