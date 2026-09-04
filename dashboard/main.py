"""
Phase 1 dashboard — single Web Service compatible.
Adds session middleware + auth/settings/discord-meta routers on top of
the Phase 0 health check.
"""

import os
import sys
import logging

# Ensure project root is on path (mirrors bot/main.py's pattern)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import text

from shared.db_models import Base
from dashboard.core.db import engine
from dashboard import config
from dashboard.api import auth, settings as settings_api, discord_meta

logging.basicConfig(level="INFO")
log = logging.getLogger("dashboard")

app = FastAPI(title="Trading Bot Dashboard API")

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    same_site="lax",
    https_only=config.COOKIE_HTTPS_ONLY,
)

app.include_router(auth.router)
app.include_router(settings_api.router)
app.include_router(discord_meta.router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Dashboard connected to database.")


@app.get("/api/health")
async def health():
    db_status = "connected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        log.exception("Health check DB query failed")
        db_status = f"error: {e}"
    return {"status": "ok", "db": db_status}
