from __future__ import annotations

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.util.coroutine_util import run_coro


async def unsettimezone_cmd(interaction: discord.Interaction, bot: Bot) -> None:
    guild_state = bot.guild_states[interaction.guild_id]
    guild_state.timezone = None
    conn = await bot.pool_acquire()
    try:
        await conn.execute('UPDATE guild SET timezone=NULL WHERE id=$1', interaction.guild_id)
    finally:
        await bot.pool_release(conn)
    await run_coro(interaction.response.send_message('Custom timezone unset.'))
