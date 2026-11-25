from __future__ import annotations

from collections import Counter

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from laro.domain.bot import Bot
from laro.domain.models import ChannelState, EntryLog, Mvp
from laro.domain.track_type import TrackType
from laro.util import track_util


def find_entry(bot: Bot, query: str) -> list[Mvp]:
    """Find MVPs whose name (or alias) matches the query.

    An exact match short-circuits the search. Otherwise every entry whose
    full name (name + map) or alias starts with the query is returned.
    """
    exact_matches = [entry for entry in bot.mvp_list if _entry_exact_match(entry, query)]
    if exact_matches:
        return exact_matches
    return [entry for entry in bot.mvp_list if _entry_matches(entry, query)]


def _entry_compare(entry: Mvp) -> list[str]:
    map_refs = [entry.map] if entry.navi is None else [entry.navi, entry.map]
    compares = [entry.name]
    compares.extend(entry.name + ' ' + ref for ref in map_refs)
    compares.extend(entry.alias)
    compares.extend(alias + ' ' + ref for alias in entry.alias for ref in map_refs)
    return compares


def _entry_exact_match(entry: Mvp, query: str) -> bool:
    return query.lower() in map(str.lower, _entry_compare(entry))


def _entry_matches(entry: Mvp, query: str) -> bool:
    query_lower = query.lower()
    return any(c.lower().startswith(query_lower) for c in _entry_compare(entry))


def ac_entries(bot: Bot, query: str) -> list[tuple[str, str]]:
    """Autocomplete entries for the /track command, as (label, value) pairs.

    Same prefix semantics as find_entry. When two MVPs share a name (same
    name, different maps), the map disambiguates both the label and the
    value, mirroring find_entry's 'name map' exact-match syntax. At most
    the 25 options the Discord autocomplete allows.
    """
    if not query:
        return []
    matched = [entry for entry in bot.mvp_list if _entry_matches(entry, query)]
    name_counts = Counter(entry.name.lower() for entry in matched)
    results: list[tuple[str, str]] = []
    for entry in matched:
        if name_counts[entry.name.lower()] > 1:
            results.append((f'{entry.name} ({entry.display_map})', f'{entry.name} {entry.display_map}'))
        else:
            results.append((entry.name, entry.name))
        if len(results) == 25:
            break
    return results


async def load_db_entries(bot: Bot, conn: asyncpg.Connection) -> None:
    db_entry_guild_list = await conn.fetch('SELECT * FROM mvp_guild')
    db_entry_log_list = await conn.fetch('SELECT * FROM mvp_guild_log ORDER BY date DESC')
    entries_by_id = {entry.id: entry for entry in bot.mvp_list}
    for guild_state in bot.guild_states.values():
        channel_state = guild_state.get_channel_state(TrackType.MVP)
        if channel_state is None:
            continue
        await _restore_channel_entries(
            bot,
            conn,
            channel_state,
            db_entry_guild_list,
            db_entry_log_list,
            entries_by_id,
        )


async def load_channel_entries(
    bot: Bot, conn: asyncpg.Connection | PoolConnectionProxy, channel_state: ChannelState
) -> None:
    """Restore persisted entries and recent history for a newly configured channel."""
    db_entry_guild_list = await conn.fetch('SELECT * FROM mvp_guild WHERE id_guild=$1', channel_state.id_guild)
    db_entry_log_list = await conn.fetch(
        'SELECT * FROM mvp_guild_log WHERE id_guild=$1 ORDER BY date DESC', channel_state.id_guild
    )
    entries_by_id = {entry.id: entry for entry in bot.mvp_list}
    await _restore_channel_entries(
        bot,
        conn,
        channel_state,
        db_entry_guild_list,
        db_entry_log_list,
        entries_by_id,
    )


async def _restore_channel_entries(
    bot: Bot,
    conn: asyncpg.Connection | PoolConnectionProxy,
    channel_state: ChannelState,
    db_entry_guild_list,
    db_entry_log_list,
    entries_by_id: dict[int, Mvp],
) -> None:
    for db_entry_guild in db_entry_guild_list:
        if db_entry_guild['id_guild'] != channel_state.id_guild:
            continue
        entry = entries_by_id.get(db_entry_guild['id_mvp'])
        if entry is None:
            continue
        entry_state = track_util.track_entry(channel_state, entry, db_entry_guild['track_time'])
        # track_entry resets notified; restore the persisted value to avoid a
        # duplicate ping when an already-open window survives a restart.
        entry_state.notified = db_entry_guild['notified']

    for db_entry_log in db_entry_log_list:
        if db_entry_log['id_guild'] != channel_state.id_guild:
            continue
        entry = entries_by_id.get(db_entry_log['id_mvp'])
        if entry is None:
            continue
        if len(channel_state.entry_logs) < 3:
            channel_state.entry_logs.append(
                EntryLog(entry=entry, date=db_entry_log['date'], id_user=db_entry_log['id_user'])
            )
        else:
            entry_state = next((x for x in channel_state.entry_states if x.entry is entry), None)
            if entry_state is not None and entry_state.r2 <= -bot.settings.table_entry_expiration_mins:
                await conn.execute(
                    'DELETE FROM mvp_guild WHERE id_guild=$1 AND id_mvp=$2',
                    db_entry_log['id_guild'],
                    db_entry_log['id_mvp'],
                )
