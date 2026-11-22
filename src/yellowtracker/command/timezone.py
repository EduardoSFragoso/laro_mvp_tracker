from __future__ import annotations

import discord
import pytz

from yellowtracker.domain.bot import Bot
from yellowtracker.util.coroutine_util import run_coro


async def timezone_cmd(interaction: discord.Interaction, bot: Bot, timezone: str) -> None:
    if timezone not in pytz.all_timezones:
        msg = 'Timezone "' + timezone + '" is invalid.'
        msg += '\n'
        msg += '\nExamples of valid timezones can be found here (TZ Identifier column):'
        msg += '\nhttps://en.wikipedia.org/wiki/List_of_tz_database_time_zones#Time_Zone_abbreviations'
    else:
        guild_state = bot.guild_states[interaction.guild_id]
        guild_state.timezone = timezone
        conn = await bot.pool_acquire()
        try:
            await conn.execute('UPDATE guild SET timezone=$2 WHERE id=$1', interaction.guild_id, timezone)
        finally:
            await bot.pool_release(conn)
        msg = 'Custom timezone set to ' + timezone + '.'
    await run_coro(interaction.response.send_message(msg))
