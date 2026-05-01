"""
ReadyDay — FastAPI app entry point
Dev:  uvicorn main:app --reload
Prod: Railway / Render (Dockerfile o Procfile)
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from logging_utils import setup_logging
from routers import scores, defaults, overrides

setup_logging()

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="ReadyDay API",
    description="Score engine + recommendation engine para ReadyDay.",
    version="0.1.0",
)

# ── CORS ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────
app.include_router(scores.router)
app.include_router(defaults.router)
app.include_router(overrides.router)


# ── Health check ─────────────────────────────
@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "readyday-api"}


# ── Web app (HTML MVP) ────────────────────────
# Sirve mvp/ como static files. En producción (Railway),
# el MVP queda accesible en / para el socio.
_MVP_DIR = Path(__file__).parent.parent / "mvp"

if _MVP_DIR.exists():
    # /founders.html y otros assets del mvp/
    app.mount("/app", StaticFiles(directory=str(_MVP_DIR), html=True), name="mvp")

    @app.get("/", tags=["web"], include_in_schema=False)
    def serve_index():
        """Sirve el HTML MVP en la raíz — acceso directo para socios."""
        return FileResponse(str(_MVP_DIR / "index.html"))
else:
    @app.get("/", tags=["meta"])
    def root():
        return {
            "service": "ReadyDay API",
            "version": "0.1.0",
            "docs": "/docs",
        }
