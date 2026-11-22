from __future__ import annotations

import discord
from yellowtracker.domain.bot import Bot
from yellowtracker.service import channel_service
from yellowtracker.util.coroutine_util import run_coro


async def mobile(interaction: discord.Interaction, bot: Bot) -> None:
    guild_state = bot.guild_states[interaction.guild_id]
    mobile = not guild_state.mobile
    guild_state.mobile = mobile
    conn = await bot.pool_acquire()
    try:
        await conn.execute('UPDATE guild SET mobile=$2 WHERE id=$1', interaction.guild_id, mobile)
    finally:
        await bot.pool_release(conn)
    msg = 'MVP list mobile layout ' + ('enabled.' if mobile else 'disabled.')
    channel_state = guild_state.channel_states.get(interaction.channel_id)
    await run_coro(interaction.response.send_message(msg))
    await channel_service.update_channel_message(bot, channel_state)
