from __future__ import annotations

import logging

import discord

from laro.domain.bot import Bot


log = logging.getLogger(__name__)


async def on_guild_remove(guild: discord.Guild, bot: Bot) -> None:
    log.info(f'Withdrawn from {guild.name}.')
    conn = await bot.pool_acquire()
    try:
        async with conn.transaction():
            await conn.execute('DELETE FROM mvp_guild WHERE id_guild=$1', guild.id)
            await conn.execute('DELETE FROM guild WHERE id=$1', guild.id)
        bot.guild_states.pop(guild.id, None)
    finally:
        await bot.pool_release(conn)
