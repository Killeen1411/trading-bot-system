"""
Shared SQLAlchemy models — imported by BOTH bot/ and dashboard/.
Phase 1 adds: expanded GuildSettings, DashboardUser (OAuth sessions),
GuildMetaCache (channel/role cache the bot fills, dashboard reads).
"""

from sqlalchemy import BigInteger, String, DateTime, Boolean, Integer, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GuildSettings(Base):
    """
    Expanded for Phase 1 with the fields the Settings page needs.
    display_timezones is a JSON list of IANA tz names, e.g.
    ["Asia/Kolkata", "UTC", "America/New_York"] — used by embed_builder's
    {time} rendering (added in Phase 2/5).
    """
    __tablename__ = "guild_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    admin_log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    default_timezone: Mapped[str] = mapped_column(String, default="Asia/Kolkata")
    display_timezones: Mapped[list] = mapped_column(
        JSON, default=lambda: ["Asia/Kolkata", "UTC", "America/New_York"]
    )
    daily_brief_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_brief_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    daily_brief_time_utc: Mapped[str | None] = mapped_column(String, nullable=True)  # "HH:MM", 24h UTC
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<GuildSettings guild_id={self.guild_id}>"


class DashboardUser(Base):
    """
    One row per person who has logged into the dashboard via Discord OAuth.
    guild_id is fixed to the single managed guild (this isn't a multi-tenant
    bot), stored per-user mainly so future permission tiers have somewhere
    to hang off `role`.
    """
    __tablename__ = "dashboard_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    role: Mapped[str] = mapped_column(String, default="admin")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<DashboardUser discord_user_id={self.discord_user_id}>"


class GuildMetaCache(Base):
    """
    Bot writes, dashboard reads. Avoids the dashboard needing its own bot
    token or gateway connection just to populate channel/role dropdowns —
    see bot/cogs/discord_meta_sync.py for the writer side.
    """
    __tablename__ = "guild_meta_cache"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guild_name: Mapped[str | None] = mapped_column(String, nullable=True)
    guild_icon_url: Mapped[str | None] = mapped_column(String, nullable=True)
    member_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channels: Mapped[list] = mapped_column(JSON, default=list)  # [{id, name, category_name, position}]
    roles: Mapped[list] = mapped_column(JSON, default=list)     # [{id, name, color_hex, mentionable, position}]
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<GuildMetaCache guild_id={self.guild_id}>"


# NOTE for future phases:
# - Phase 2 adds EmbedTemplate
# - Phase 3 adds PendingAction
# - Phase 4 adds Killzone, KillzoneEventsLog
# - Phase 5/6 add NewsSource, PostedNews, EconomicEvent
# - Phase 7 adds StockResultsCalendar
