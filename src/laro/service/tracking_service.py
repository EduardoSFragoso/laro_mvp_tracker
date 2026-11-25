from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import discord

from laro.domain.bot import Bot
from laro.domain.models import ChannelState, EntryLog, GuildState, Mvp
from laro.domain.track_type import TrackType
from laro.service import entry_service
from laro.ui.channel_views import TrackView
from laro.util import track_util
from laro.util.coroutine_util import run_coro
from laro.util.date_util import get_dt_now


def parse_user_time(timezone: str, user_time: str) -> datetime | str:
    """Convert ``HHMM`` into a datetime in the recent past for a timezone."""
    if not (user_time.isnumeric() and len(user_time) == 4):
        return 'HHMM format expected for user time'
    hh = int(user_time[:2])
    mm = int(user_time[2:])
    if hh > 23:
        return 'HH must be between 00 and 23'
    if mm > 59:
        return 'MM must be between 00 and 59'
    track_time = get_dt_now(timezone)
    if hh > track_time.hour or (hh == track_time.hour and mm > track_time.minute):
        track_time -= timedelta(days=1)
    return track_time.replace(hour=hh, minute=mm)


def _resolve_query(
    bot: Bot, guild_state: Any, channel_state: ChannelState, mvp: str, user_time: str | None
) -> tuple[list[Mvp], int, str | None]:
    """Resolve an MVP query and optional user time into matches and elapsed minutes."""
    mins_ago = 0
    if user_time is not None:
        timezone = guild_state.timezone or bot.settings.timezone
        parsed = parse_user_time(timezone, user_time)
        if isinstance(parsed, str):
            return [], 0, parsed
        mins_ago = int((get_dt_now(timezone) - parsed) / timedelta(minutes=1))
    results = entry_service.find_entry(bot, mvp)
    return results, mins_ago, None


async def track_by_message(
    bot: Bot, message: discord.Message, channel_state: ChannelState, mvp: str, user_time: str | None
) -> None:
    guild_state = bot.get_guild_state(channel_state.id_guild)
    if guild_state is None:
        return
    results, mins_ago, error = _resolve_query(bot, guild_state, channel_state, mvp, user_time)
    if error is not None:
        await run_coro(message.channel.send(error))
        return
    await _dispatch_track(
        bot,
        guild_state,
        channel_state,
        results,
        mins_ago,
        user_time,
        message.author.id,
        mvp,
        MessageSender(message.channel),
    )


async def track_by_interaction(
    bot: Bot, interaction: discord.Interaction, channel_state: ChannelState, mvp: str, user_time: str | None
) -> None:
    guild_state = bot.get_guild_state(channel_state.id_guild)
    if guild_state is None:
        return
    results, mins_ago, error = _resolve_query(bot, guild_state, channel_state, mvp, user_time)
    if error is not None:
        await run_coro(interaction.response.send_message(error))
        return
    await _dispatch_track(
        bot,
        guild_state,
        channel_state,
        results,
        mins_ago,
        user_time,
        interaction.user.id,
        mvp,
        InteractionSender(interaction),
    )


async def _dispatch_track(
    bot: Bot,
    guild_state: GuildState,
    channel_state: ChannelState,
    results: list[Mvp],
    mins_ago: int,
    user_time: str | None,
    id_user: int,
    mvp: str,
    sender: MessageSender | InteractionSender,
) -> None:
    track_type = channel_state.type
    if not results:
        await run_coro(sender.send(f'{track_type.desc} "{mvp}" not found.'))
    elif len(results) == 1:
        bot_reply_msg = await update_track_time(
            bot, guild_state, channel_state, results[0], mins_ago, user_time, id_user
        )
        await run_coro(sender.send(bot_reply_msg))
    else:
        msg = _multiple_matches_msg(track_type, mvp, user_time)
        await run_coro(sender.send(msg, view=TrackView(bot=bot, opts=results, mins_ago=mins_ago, user_time=user_time)))


def _multiple_matches_msg(track_type: TrackType, query: str, user_time: str | None) -> str:
    msg = 'More than one ' + track_type.desc
    msg += ' starting with "' + query + '" has been found.\n\n'
    msg += 'Select the ' + track_type.desc + ' that you want to track'
    if user_time is not None:
        msg += ' with time ' + user_time
    msg += ':'
    return msg


class MessageSender:
    """Send messages through a text channel."""

    def __init__(self, channel: discord.abc.Messageable):
        self.channel = channel

    async def send(self, content: str, **kwargs: Any):
        return await self.channel.send(content, **kwargs)


class InteractionSender:
    """Send responses through a Discord interaction."""

    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction

    async def send(self, content: str, **kwargs: Any):
        return await self.interaction.response.send_message(content, **kwargs)


async def update_track_time(
    bot: Bot,
    guild_state: GuildState,
    channel_state: ChannelState,
    entry: Mvp,
    mins_ago: int,
    user_time: str | None,
    id_user: int,
) -> str:
    row_sql = channel_state.type.sql_desc
    date = datetime.now()
    track_time = date - timedelta(minutes=mins_ago)
    updated_logs = [x for x in channel_state.entry_logs if x.entry is not entry]
    updated_logs.insert(0, EntryLog(entry=entry, date=date, id_user=id_user))
    removed_logs = updated_logs[3:]
    updated_logs = updated_logs[:3]
    conn = await bot.pool_acquire()
    try:
        async with conn.transaction():
            upsert_entry_sql = (
                f'INSERT INTO {row_sql}_guild(id_{row_sql},id_guild,track_time) VALUES($1,$2,$3) '
                f'ON CONFLICT (id_{row_sql},id_guild) '
                'DO UPDATE SET track_time=EXCLUDED.track_time, notified=FALSE'
            )
            await conn.execute(upsert_entry_sql, entry.id, channel_state.id_guild, track_time)

            upsert_log_sql = (
                f'INSERT INTO {row_sql}_guild_log(id_{row_sql},id_guild,date,id_user) VALUES($1,$2,$3,$4) '
                f'ON CONFLICT (id_{row_sql},id_guild) '
                'DO UPDATE SET date=EXCLUDED.date, id_user=EXCLUDED.id_user'
            )
            await conn.execute(upsert_log_sql, entry.id, channel_state.id_guild, date, id_user)

            for removed_log in removed_logs:
                del_sql = f'DELETE FROM {row_sql}_guild_log WHERE id_{row_sql}=$1 AND id_guild=$2'
                await conn.execute(del_sql, removed_log.entry.id, channel_state.id_guild)
    finally:
        await bot.pool_release(conn)

    channel_state.entry_logs.clear()
    channel_state.entry_logs.extend(updated_logs)
    entry_state = track_util.track_entry(channel_state, entry, track_time, custom=guild_state.custom)
    from laro.service import channel_service

    await channel_service.update_channel_message(bot, channel_state)
    return _fmt_track_reply(entry_state, user_time)


def _fmt_track_reply(entry_state, user_time: str | None) -> str:
    msg = f'{entry_state.entry.name} ({entry_state.entry.display_map}) in '
    msg += track_util.fmt_r1_r2(int(entry_state.r1))
    msg += ' to ' + track_util.fmt_r1_r2(int(entry_state.r2)) + ' minutes'
    if user_time is not None:
        msg += f' (time: {user_time})'
    return msg + '.'
