"""
GET/PATCH /api/settings — the single guild_settings row for the managed guild.
Auto-creates the row on first access so the frontend never has to handle
a "settings don't exist yet" 404 case.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_models import DashboardUser, GuildSettings
from dashboard.core.db import get_session
from dashboard.core.security import get_current_dashboard_user
from dashboard import config

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    admin_log_channel_id: int | None = None
    default_timezone: str | None = None
    display_timezones: list[str] | None = None
    daily_brief_enabled: bool | None = None
    daily_brief_channel_id: int | None = None
    daily_brief_time_utc: str | None = None


async def _get_or_create_settings(session: AsyncSession) -> GuildSettings:
    result = await session.execute(select(GuildSettings).where(GuildSettings.guild_id == config.GUILD_ID))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = GuildSettings(guild_id=config.GUILD_ID)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


def _serialize(settings: GuildSettings) -> dict:
    return {
        "guild_id": settings.guild_id,
        "admin_log_channel_id": settings.admin_log_channel_id,
        "default_timezone": settings.default_timezone,
        "display_timezones": settings.display_timezones,
        "daily_brief_enabled": settings.daily_brief_enabled,
        "daily_brief_channel_id": settings.daily_brief_channel_id,
        "daily_brief_time_utc": settings.daily_brief_time_utc,
    }


@router.get("")
async def get_settings(
    session: AsyncSession = Depends(get_session),
    _user: DashboardUser = Depends(get_current_dashboard_user),
):
    settings = await _get_or_create_settings(session)
    return _serialize(settings)


@router.patch("")
async def update_settings(
    body: SettingsUpdate,
    session: AsyncSession = Depends(get_session),
    _user: DashboardUser = Depends(get_current_dashboard_user),
):
    settings = await _get_or_create_settings(session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await session.commit()
    await session.refresh(settings)
    return _serialize(settings)
