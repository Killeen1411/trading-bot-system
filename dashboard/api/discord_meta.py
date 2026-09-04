"""
GET /api/discord/channels, /roles, /guild-info — reads from guild_meta_cache,
which bot/cogs/discord_meta_sync.py keeps fresh every few minutes. The
dashboard never talks to Discord directly for this.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_models import DashboardUser, GuildMetaCache
from dashboard.core.db import get_session
from dashboard.core.security import get_current_dashboard_user
from dashboard import config

router = APIRouter(prefix="/api/discord", tags=["discord-meta"])


async def _get_cache(session: AsyncSession) -> GuildMetaCache:
    result = await session.execute(select(GuildMetaCache).where(GuildMetaCache.guild_id == config.GUILD_ID))
    cache = result.scalar_one_or_none()
    if cache is None:
        raise HTTPException(status_code=503, detail="Guild data not synced yet — the bot may still be starting up")
    return cache


@router.get("/channels")
async def get_channels(
    session: AsyncSession = Depends(get_session),
    _user: DashboardUser = Depends(get_current_dashboard_user),
):
    cache = await _get_cache(session)
    return cache.channels


@router.get("/roles")
async def get_roles(
    session: AsyncSession = Depends(get_session),
    _user: DashboardUser = Depends(get_current_dashboard_user),
):
    cache = await _get_cache(session)
    return cache.roles


@router.get("/guild-info")
async def get_guild_info(
    session: AsyncSession = Depends(get_session),
    _user: DashboardUser = Depends(get_current_dashboard_user),
):
    cache = await _get_cache(session)
    return {
        "id": cache.guild_id,
        "name": cache.guild_name,
        "icon_url": cache.guild_icon_url,
        "member_count": cache.member_count,
    }
