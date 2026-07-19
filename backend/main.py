"""
ReadyDay API — FastAPI entry point
Dev:  uvicorn main:app --reload --port 8001
Prod: Docker + Caddy reverse proxy en /readyday
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config import get_settings
from database import init_db
from scheduler import start_scheduler

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(
    title="ReadyDay API",
    description="Score engine multi-wearable para readiness diario.",
    version="1.0.0",
    lifespan=lifespan,
    # root_path vacío: Caddy hace handle_path y le quita /readyday antes de reenviar
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from routers import auth, snapshots, scores, devices, notifications  # noqa
app.include_router(auth.router)
app.include_router(snapshots.router)
app.include_router(scores.router)
app.include_router(devices.router)
app.include_router(notifications.router)


# Health check (sin auth)
@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "readyday-api", "version": "1.0.0"}


# Servir el frontend web desde /frontend
_FRONTEND = Path(__file__).parent.parent / "frontend"
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND)), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str = ""):
        index = _FRONTEND / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"message": "Frontend not found"}
