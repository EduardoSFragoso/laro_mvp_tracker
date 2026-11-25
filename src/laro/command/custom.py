from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.util.coroutine_util import run_coro


async def custom_core(bot: Bot, message: discord.Message) -> None:
    if message.guild is None:
        return
    guild_state = bot.get_guild_state(message.guild.id)
    if guild_state is None:
        return
    custom = not guild_state.custom
    conn = await bot.pool_acquire()
    try:
        await conn.execute('UPDATE guild SET custom=$2 WHERE id=$1', message.guild.id, custom)
        guild_state.custom = custom
    finally:
        await bot.pool_release(conn)
    msg = 'Custom MVP respawn times ' + ('enabled.' if custom else 'disabled.')
    await run_coro(message.channel.send(msg))
