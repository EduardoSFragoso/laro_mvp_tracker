from __future__ import annotations

import asyncpg
from yellowtracker.domain.bot import Bot
from yellowtracker.domain.models import EntryLog, MiningLocation, Mvp, TrackEntryState
from yellowtracker.domain.track_type import TrackType
from yellowtracker.util import track_util


def find_entry(bot: Bot, query: str, type: TrackType) -> list:
    """Find MVPs/mining locations whose name (or alias) matches the query.

    An exact match short-circuits the search. Otherwise every entry whose
    full name (name + map for MVPs) or alias starts with the query is returned.
    """
    entry_list = bot.mvp_list if type == TrackType.MVP else bot.mining_list
    results = []
    for entry in entry_list:
        if _entry_matches(entry, query, type):
            results.append(entry)
            if _entry_exact_match(entry, query, type):
                return [entry]
    return results


def _entry_compare(entry, type: TrackType) -> list[str]:
    compares = [entry.name]
    if type == TrackType.MVP:
        compares.append(entry.name + ' ' + entry.map)
        compares.extend(alias + ' ' + entry.map for alias in entry.alias)
    compares.extend(entry.alias)
    return compares


def _entry_exact_match(entry, query: str, type: TrackType) -> bool:
    return query.lower() in map(str.lower, _entry_compare(entry, type))


def _entry_matches(entry, query: str, type: TrackType) -> bool:
    query_lower = query.lower()
    return any(c.lower().startswith(query_lower) for c in _entry_compare(entry, type))


async def load_db_entries(bot: Bot, conn, type: TrackType) -> None:
    entry_list = bot.mvp_list if type == TrackType.MVP else bot.mining_list
    db_entry_guild_list = await conn.fetch('SELECT * FROM ' + type.sql_desc + '_guild')
    for db_entry_guild in db_entry_guild_list:
        guild_state = bot.guild_states.get(db_entry_guild['id_guild'])
        if guild_state is None:
            continue
        entry = next(
            (x for x in entry_list if x.id == db_entry_guild['id_' + type.sql_desc]),
            None,
        )
        if entry is None:
            continue
        channel_state = guild_state.get_channel_state(type)
        if channel_state is None:
            continue
        track_util.track_entry(channel_state, entry, db_entry_guild['track_time'])
    await _load_db_entries_log(bot, conn, type)


async def _load_db_entries_log(bot: Bot, conn, type: TrackType) -> None:
    sql = f"SELECT * FROM {type.sql_desc}_guild_log ORDER BY date DESC"
    db_entry_log_list = await conn.fetch(sql)
    entry_list = bot.mvp_list if type == TrackType.MVP else bot.mining_list
    for db_entry_log in db_entry_log_list:
        guild_state = bot.guild_states.get(db_entry_log['id_guild'])
        if guild_state is None:
            continue
        entry = next(
            (x for x in entry_list if x.id == db_entry_log['id_' + type.sql_desc]),
            None,
        )
        if entry is None:
            continue
        channel_state = guild_state.get_channel_state(type)
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
            if entry_state is not None:
                rtime = entry_state.r2 if type == TrackType.MVP else entry_state.r1
                if rtime <= -bot.settings.table_entry_expiration_mins:
                    delete_sql = (
                        f"DELETE FROM {type.sql_desc}_guild "
                        f"WHERE id_guild=$1 AND id_{type.sql_desc}=$2"
                    )
                    await conn.execute(
                        delete_sql,
                        db_entry_log['id_guild'],
                        db_entry_log['id_' + type.sql_desc],
                    )
