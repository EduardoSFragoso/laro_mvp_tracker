from __future__ import annotations

import asyncpg

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.models import EntryLog, Mvp
from yellowtracker.domain.track_type import TrackType
from yellowtracker.util import track_util


def find_entry(bot: Bot, query: str) -> list[Mvp]:
    """Find MVPs whose name (or alias) matches the query.

    An exact match short-circuits the search. Otherwise every entry whose
    full name (name + map) or alias starts with the query is returned.
    """
    results = []
    for entry in bot.mvp_list:
        if _entry_matches(entry, query):
            results.append(entry)
            if _entry_exact_match(entry, query):
                return [entry]
    return results


def _entry_compare(entry: Mvp) -> list[str]:
    compares = [entry.name, entry.name + ' ' + entry.map]
    compares.extend(entry.alias)
    compares.extend(alias + ' ' + entry.map for alias in entry.alias)
    return compares


def _entry_exact_match(entry: Mvp, query: str) -> bool:
    return query.lower() in map(str.lower, _entry_compare(entry))


def _entry_matches(entry: Mvp, query: str) -> bool:
    query_lower = query.lower()
    return any(c.lower().startswith(query_lower) for c in _entry_compare(entry))


async def load_db_entries(bot: Bot, conn: asyncpg.Connection) -> None:
    db_entry_guild_list = await conn.fetch('SELECT * FROM mvp_guild')
    for db_entry_guild in db_entry_guild_list:
        guild_state = bot.guild_states.get(db_entry_guild['id_guild'])
        if guild_state is None:
            continue
        entry = next(
            (x for x in bot.mvp_list if x.id == db_entry_guild['id_mvp']),
            None,
        )
        if entry is None:
            continue
        channel_state = guild_state.get_channel_state(TrackType.MVP)
        if channel_state is None:
            continue
        track_util.track_entry(channel_state, entry, db_entry_guild['track_time'])
    await _load_db_entries_log(bot, conn)


async def _load_db_entries_log(bot: Bot, conn: asyncpg.Connection) -> None:
    sql = 'SELECT * FROM mvp_guild_log ORDER BY date DESC'
    db_entry_log_list = await conn.fetch(sql)
    for db_entry_log in db_entry_log_list:
        guild_state = bot.guild_states.get(db_entry_log['id_guild'])
        if guild_state is None:
            continue
        entry = next(
            (x for x in bot.mvp_list if x.id == db_entry_log['id_mvp']),
            None,
        )
        if entry is None:
            continue
        channel_state = guild_state.get_channel_state(TrackType.MVP)
        if channel_state is None:
            continue
        if len(channel_state.entry_logs) < 3:
            channel_state.entry_logs.append(
                EntryLog(entry=entry, date=db_entry_log['date'], id_user=db_entry_log['id_user'])
            )
        else:
            entry_state = next(
                (x for x in channel_state.entry_states if x.entry is entry),
                None,
            )
            if entry_state is not None and entry_state.r2 <= -bot.settings.table_entry_expiration_mins:
                delete_sql = 'DELETE FROM mvp_guild WHERE id_guild=$1 AND id_mvp=$2'
                await conn.execute(
                    delete_sql,
                    db_entry_log['id_guild'],
                    db_entry_log['id_mvp'],
                )
