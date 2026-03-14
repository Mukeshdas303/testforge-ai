import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.test_generation import router

logging.basicConfig(
    level   = logging.DEBUG if settings.debug else logging.INFO,
    format  = "%(asctime)s | %(levelname)-8s | %(name)s — %(message)s"
)

app = FastAPI(
    title       = settings.app_name,
    version     = settings.app_version,
    description = "AI-powered test case generation using Ollama phi3 LLM",
    docs_url    = "/docs",
    redoc_url   = "/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs":    "/docs"
    }
    