from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.service import channel_service
from laro.util.coroutine_util import run_coro


async def mobile_core(bot: Bot, message: discord.Message) -> None:
    if message.guild is None:
        return
    guild_state = bot.get_guild_state(message.guild.id)
    if guild_state is None:
        return
    mobile = not guild_state.mobile
    guild_state.mobile = mobile
    conn = await bot.pool_acquire()
    try:
        await conn.execute('UPDATE guild SET mobile=$2 WHERE id=$1', message.guild.id, mobile)
    finally:
        await bot.pool_release(conn)
    msg = 'MVP list mobile layout ' + ('enabled.' if mobile else 'disabled.')
    channel_state = guild_state.channel_states.get(message.channel.id)
    await run_coro(message.channel.send(msg))
    if channel_state is not None:
        await channel_service.update_channel_message(bot, channel_state)
