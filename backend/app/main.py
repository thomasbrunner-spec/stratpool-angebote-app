"""
FastAPI application entry point.

Run locally:
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.routes import health, hello

settings = get_settings()


# ---------------- Logging Setup ----------------
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>",
    level="DEBUG" if settings.debug else "INFO",
)


# ---------------- Lifespan ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    logger.info(f"🚀 Starting {settings.app_name} ({settings.environment})")
    logger.info(f"Anthropic model: {settings.anthropic_model}")
    logger.info(f"Voyage model: {settings.voyage_model}")
    yield
    logger.info(f"👋 Shutting down {settings.app_name}")


# ---------------- App ----------------
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# CORS – allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- Routes ----------------
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(hello.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint — points to docs."""
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
