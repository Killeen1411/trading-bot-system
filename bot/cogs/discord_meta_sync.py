"""
Periodically syncs the managed guild's channels and roles into
guild_meta_cache, so the dashboard can populate channel/role pickers
without needing its own bot token or gateway connection.
"""

import logging
from discord.ext import commands, tasks
from sqlalchemy import select

from shared.db_models import GuildMetaCache
from bot.config import GUILD_ID

log = logging.getLogger("discord_meta_sync")

SYNC_INTERVAL_MINUTES = 5


class DiscordMetaSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sync_meta.start()

    def cog_unload(self):
        self.sync_meta.cancel()

    @tasks.loop(minutes=SYNC_INTERVAL_MINUTES)
    async def sync_meta(self):
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            log.warning(f"Guild {GUILD_ID} not found — is the bot actually a member of it?")
            return

        channels = [
            {
                "id": c.id,
                "name": c.name,
                "category_name": c.category.name if c.category else None,
                "position": c.position,
            }
            for c in guild.text_channels
        ]
        roles = [
            {
                "id": r.id,
                "name": r.name,
                "color_hex": str(r.color),
                "mentionable": r.mentionable,
                "position": r.position,
            }
            for r in guild.roles
            if r.name != "@everyone"
        ]

        async with self.bot.session_maker() as session:
            result = await session.execute(select(GuildMetaCache).where(GuildMetaCache.guild_id == guild.id))
            cache = result.scalar_one_or_none()
            if cache is None:
                cache = GuildMetaCache(guild_id=guild.id)
                session.add(cache)

            cache.guild_name = guild.name
            cache.guild_icon_url = guild.icon.url if guild.icon else None
            cache.member_count = guild.member_count
            cache.channels = channels
            cache.roles = roles

            await session.commit()

        log.info(f"Synced {len(channels)} channels and {len(roles)} roles for guild {guild.id}")

    @sync_meta.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DiscordMetaSync(bot))
