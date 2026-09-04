"""
Thin wrapper around Discord's OAuth2 token exchange and the two REST
endpoints we need (@me, @me/guilds). No bot token involved here — this is
purely the user's own OAuth access token.
"""

from urllib.parse import urlencode

import httpx

DISCORD_API = "https://discord.com/api/v10"
MANAGE_GUILD_PERMISSION = 0x20  # bit flag Discord returns in @me/guilds


def build_authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
        "prompt": "consent",
    }
    return f"https://discord.com/oauth2/authorize?{urlencode(params)}"


async def exchange_code_for_token(code: str, client_id: str, client_secret: str, redirect_uri: str) -> dict:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{DISCORD_API}/oauth2/token", data=data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def fetch_discord_user(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{DISCORD_API}/users/@me", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def fetch_user_guilds(access_token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{DISCORD_API}/users/@me/guilds", headers=headers)
        resp.raise_for_status()
        return resp.json()
