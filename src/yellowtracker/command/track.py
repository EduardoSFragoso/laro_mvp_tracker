from __future__ import annotations

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.service import channel_service
from yellowtracker.util.coroutine_util import run_coro


async def track(interaction: discord.Interaction, bot: Bot, mvp: str, user_time: str) -> None:
    validate_msg = channel_service.validate_channel(bot, interaction.channel)
    if validate_msg is not None:
        await run_coro(interaction.response.send_message(validate_msg))
        return
    guild_state = bot.guild_states[interaction.guild_id]
    channel_state = guild_state.channel_states.get(interaction.channel_id)
    if channel_state is None:
        await run_coro(interaction.response.send_message('This command can only be used in a track channel.'))
        return
    await channel_service.track_by_interaction(bot, interaction, channel_state, mvp, user_time)
