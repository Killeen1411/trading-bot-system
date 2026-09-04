"""
Central place for dashboard-only env vars. Mirrors bot/config.py's role —
nothing else in dashboard/ should call os.environ directly.
"""

import os

GUILD_ID = int(os.environ["GUILD_ID"])
DATABASE_URL = os.environ["DATABASE_URL"]

DISCORD_CLIENT_ID = os.environ["DISCORD_CLIENT_ID"]
DISCORD_CLIENT_SECRET = os.environ["DISCORD_CLIENT_SECRET"]
DISCORD_REDIRECT_URI = os.environ["DISCORD_REDIRECT_URI"]

SESSION_SECRET = os.environ["SESSION_SECRET"]

# Where to send the browser after a successful login. "/" for now —
# will point at the actual SPA route once the frontend exists.
DASHBOARD_BASE_URL = os.environ.get("DASHBOARD_BASE_URL", "/")

# Render serves the app over HTTPS to the browser even though the backend
# process itself speaks plain HTTP — so this should stay "true" in
# production. Only set to "false" for local http://localhost testing.
COOKIE_HTTPS_ONLY = os.environ.get("COOKIE_HTTPS_ONLY", "true").lower() == "true"
