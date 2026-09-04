"""
Phase 0 entrypoint — single Web Service compatible.
Bot + Dashboard run together via start.sh
"""

import asyncio
import logging
import os
import sys

# Ensure project root is on path (works when run as `python -m bot.main`)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import discord
from discord.ext import commands
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from shared.db_models import Base
from bot.config import DISCORD_TOKEN, GUILD_ID, DATABASE_URL, LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("bot")

INTENTS = discord.Intents.default()
INTENTS.message_content = False
INTENTS.guilds = True


class TradingBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)
        self.engine = None
        self.session_maker: async_sessionmaker[AsyncSession] | None = None

    async def setup_hook(self):
        db_url = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        # Render sometimes gives postgresql:// — normalize
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(db_url, echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("Database connected and tables ensured.")

        await self.load_extension("bot.cogs.discord_meta_sync")
        log.info("Loaded discord_meta_sync cog")

        try:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Slash commands synced.")
        except Exception as e:
            log.error(f"Slash command sync failed: {e}")
            log.error("Check: Bot is in the server + invited with applications.commands scope")

    async def close(self):
        if self.engine:
            await self.engine.dispose()
        await super().close()


bot = TradingBot()


@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (id={bot.user.id})")


async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
