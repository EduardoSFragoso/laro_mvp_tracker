from __future__ import annotations

import discord
from asyncpg.pool import Pool

from yellowtracker.config import Settings
from yellowtracker.domain.models import GuildState, Mvp


class Bot(discord.Client):
    """The bot client plus the shared runtime state of the application."""

    def __init__(self, settings: Settings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings
        self.pool: Pool | None = None
        self.guild_states: dict[int, GuildState] = {}
        self.mvp_list: list[Mvp] = []
        self.tracker_ready = False

    def get_guild_state(self, id_guild: int) -> GuildState | None:
        return self.guild_states.get(id_guild)

    async def pool_acquire(self):
        if self.pool is None:
            raise Exception('Pool is None')
        return await self.pool.acquire()

    async def pool_release(self, conn):
        if self.pool is None:
            raise Exception('Pool is None')
        return await self.pool.release(conn)
