from __future__ import annotations

import logging

import discord

from laro.domain.bot import Bot
from laro.domain.models import GuildState


log = logging.getLogger(__name__)


async def on_guild_join(guild: discord.Guild, bot: Bot) -> None:
    log.info(f'Joined to {guild.name}.')
    conn = await bot.pool_acquire()
    try:
        await conn.execute('INSERT INTO guild(id)VALUES($1) ON CONFLICT (id) DO NOTHING', guild.id)
        bot.guild_states[guild.id] = GuildState(id_guild=guild.id)
    finally:
        await bot.pool_release(conn)
