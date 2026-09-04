"""
Session-based auth dependency. Uses Starlette's signed-cookie SessionMiddleware
(configured in main.py) — no separate token store needed for Phase 1.
"""

from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_models import DashboardUser
from dashboard.core.db import get_session


async def get_current_dashboard_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> DashboardUser:
    discord_user_id = request.session.get("discord_user_id")
    if not discord_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await session.execute(
        select(DashboardUser).where(DashboardUser.discord_user_id == discord_user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        # Session cookie points at a user row that no longer exists —
        # clear it so the browser doesn't keep retrying a dead session.
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session invalid, please log in again")

    return user
