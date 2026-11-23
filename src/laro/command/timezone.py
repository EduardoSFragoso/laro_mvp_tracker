from __future__ import annotations

import discord
import pytz

from laro.domain.bot import Bot
from laro.util.coroutine_util import run_coro


async def timezone_core(bot: Bot, message: discord.Message, timezone: str) -> None:
    if timezone not in pytz.all_timezones:
        msg = 'Timezone "' + timezone + '" is invalid.'
        msg += '\n'
        msg += '\nExamples of valid timezones can be found here (TZ Identifier column):'
        msg += '\nhttps://en.wikipedia.org/wiki/List_of_tz_database_time_zones#Time_Zone_abbreviations'
    else:
        if message.guild is None:
            return
        guild_state = bot.get_guild_state(message.guild.id)
        if guild_state is None:
            return
        guild_state.timezone = timezone
        conn = await bot.pool_acquire()
        try:
            await conn.execute('UPDATE guild SET timezone=$2 WHERE id=$1', message.guild.id, timezone)
        finally:
            await bot.pool_release(conn)
        msg = 'Custom timezone set to ' + timezone + '.'
    await run_coro(message.channel.send(msg))
