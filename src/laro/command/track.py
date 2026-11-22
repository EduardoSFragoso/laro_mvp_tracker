from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.service import channel_service
from laro.util.coroutine_util import run_coro


async def track_core(bot: Bot, message: discord.Message, mvp: str, user_time: str | None) -> None:
    validate_msg = channel_service.validate_channel(bot, message.channel)
    if validate_msg is not None:
        await run_coro(message.channel.send(validate_msg))
        return
    guild_state = bot.get_guild_state(message.guild.id)
    if guild_state is None:
        await run_coro(message.channel.send('Bot is still starting up, try again in a moment.'))
        return
    channel_state = guild_state.channel_states.get(message.channel.id)
    if channel_state is None:
        await run_coro(message.channel.send('This command can only be used in a track channel.'))
        return
    await channel_service.track_by_message(bot, message, channel_state, mvp, user_time)
