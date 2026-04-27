"""
ReadyDay — FastAPI app entry point
Dev:  uvicorn main:app --reload
Prod: Railway / Render (Dockerfile o Procfile)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
# En prod, restringir a los dominios reales.
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


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "ReadyDay API",
        "version": "0.1.0",
        "docs": "/docs",
    }
