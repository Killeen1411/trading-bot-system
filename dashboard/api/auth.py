"""
Auth routes: /api/auth/login, /callback, /me, /logout.

Access gate: after exchanging the OAuth code, we check the user's guild
list (returned by Discord along with per-guild permission bits) for the
one managed guild, and require Manage Server permission (or ownership) to
actually get a session. Anyone can authorize the OAuth app, but only
someone who can manage the server gets into the dashboard.
"""

import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db_models import DashboardUser
from dashboard.core.db import get_session
from dashboard.core.security import get_current_dashboard_user
from dashboard.core import discord_oauth
from dashboard import config

log = logging.getLogger("auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    url = discord_oauth.build_authorize_url(config.DISCORD_CLIENT_ID, config.DISCORD_REDIRECT_URI, state)
    return RedirectResponse(url)


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    expected_state = request.session.pop("oauth_state", None)
    if not code or not state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state or missing code")

    token_data = await discord_oauth.exchange_code_for_token(
        code, config.DISCORD_CLIENT_ID, config.DISCORD_CLIENT_SECRET, config.DISCORD_REDIRECT_URI
    )
    access_token = token_data["access_token"]

    discord_user = await discord_oauth.fetch_discord_user(access_token)
    user_guilds = await discord_oauth.fetch_user_guilds(access_token)

    target_guild = next((g for g in user_guilds if int(g["id"]) == config.GUILD_ID), None)
    if target_guild is None:
        raise HTTPException(status_code=403, detail="You are not a member of the managed server")

    permissions = int(target_guild.get("permissions", 0))
    has_manage_guild = bool(permissions & discord_oauth.MANAGE_GUILD_PERMISSION)
    if not has_manage_guild and not target_guild.get("owner"):
        raise HTTPException(status_code=403, detail="Manage Server permission is required to access this dashboard")

    discord_user_id = int(discord_user["id"])
    username = discord_user.get("username")
    avatar_hash = discord_user.get("avatar")
    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{discord_user_id}/{avatar_hash}.png"
        if avatar_hash else None
    )
    now = datetime.now(timezone.utc)

    result = await session.execute(select(DashboardUser).where(DashboardUser.discord_user_id == discord_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = DashboardUser(
            discord_user_id=discord_user_id,
            username=username,
            avatar_url=avatar_url,
            guild_id=config.GUILD_ID,
            role="admin",
            last_login_at=now,
        )
        session.add(user)
    else:
        user.username = username
        user.avatar_url = avatar_url
        user.guild_id = config.GUILD_ID
        user.last_login_at = now
    await session.commit()

    request.session["discord_user_id"] = discord_user_id
    log.info(f"Dashboard login: {username} ({discord_user_id})")
    return RedirectResponse(config.DASHBOARD_BASE_URL)


@router.get("/me")
async def me(user: DashboardUser = Depends(get_current_dashboard_user)):
    return {
        "discord_user_id": user.discord_user_id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "guild_id": user.guild_id,
        "role": user.role,
    }


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"success": True}
