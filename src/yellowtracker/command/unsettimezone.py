from __future__ import annotations

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.util.coroutine_util import run_coro


async def unsettimezone_core(bot: Bot, message: discord.Message) -> None:
    guild_state = bot.get_guild_state(message.guild.id)
    if guild_state is None:
        return
    guild_state.timezone = None
    conn = await bot.pool_acquire()
    try:
        await conn.execute('UPDATE guild SET timezone=NULL WHERE id=$1', message.guild.id)
    finally:
        await bot.pool_release(conn)
    await run_coro(message.channel.send('Custom timezone unset.'))
