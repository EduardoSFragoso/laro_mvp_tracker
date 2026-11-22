from __future__ import annotations

import logging
import os

import asyncpg
import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.models import ChannelState, GuildState, MiningLocation, Mvp
from yellowtracker.domain.track_type import TrackType
from yellowtracker.service import channel_service, entry_service
from yellowtracker.util.coroutine_util import run_coro

log = logging.getLogger(__name__)


async def on_ready(bot: Bot, tree: discord.app_commands.CommandTree) -> None:
    log.info(f'Connected as {bot.user} on {len(bot.guilds)} servers.')

    if bot.settings.guild_id is not None:
        log.info(f"Sync slash commands with guild id {bot.settings.guild_id}.")
        guild_to_sync = discord.Object(id=bot.settings.guild_id)
        tree.copy_global_to(guild=guild_to_sync)
        await run_coro(tree.sync(guild=guild_to_sync))

    try:
        log.info('Create database pool.')
        bot.pool = await asyncpg.create_pool(dsn=bot.settings.database_url)
    except Exception as e:
        log.error(f'Error on database pool creation: {e}')
        os._exit(42)

    conn = await bot.pool_acquire()
    try:
        await load_database(bot, conn)
    finally:
        await bot.pool_release(conn)

    bot.tracker_ready = True


async def load_database(bot: Bot, conn) -> None:
    meta_sql = "SELECT * FROM pg_catalog.pg_tables WHERE schemaname='public' and tablename='mvp'"
    db_table_list = await conn.fetch(meta_sql)
    if len(db_table_list) == 0:
        log.error('Initial database structure not found.')
        os._exit(42)

    log.info('Load servers settings.')
    db_guild_list = await conn.fetch('SELECT * FROM guild')
    for db_guild in db_guild_list:
        if channel_service.get_guild_from_bot(bot, db_guild['id']) is None:
            await conn.execute('DELETE FROM mvp_guild WHERE id_guild=$1', db_guild['id'])
            await conn.execute('DELETE FROM mining_guild WHERE id_guild=$1', db_guild['id'])
            await conn.execute('DELETE FROM guild WHERE id=$1', db_guild['id'])
    for guild in bot.guilds:
        guild_state = GuildState(id_guild=guild.id)
        bot.guild_states[guild.id] = guild_state
        db_guild = next((x for x in db_guild_list if x['id'] == guild.id), None)
        if db_guild is None:
            await conn.execute('INSERT INTO guild(id)VALUES($1)', guild.id)
        else:
            guild_state.custom = db_guild['custom']
            guild_state.mobile = db_guild['mobile']
            guild_state.timezone = db_guild['timezone']
            guild_state.id_mvp_channel = db_guild['id_mvp_channel']
            guild_state.id_mining_channel = db_guild['id_mining_channel']
            if guild_state.id_mvp_channel is not None:
                guild_state.channel_states[guild_state.id_mvp_channel] = ChannelState(
                    id_channel=guild_state.id_mvp_channel,
                    id_guild=guild.id,
                    type=TrackType.MVP,
                )
            if guild_state.id_mining_channel is not None:
                guild_state.channel_states[guild_state.id_mining_channel] = ChannelState(
                    id_channel=guild_state.id_mining_channel,
                    id_guild=guild.id,
                    type=TrackType.MINING,
                )

    log.info('Load MVPs.')
    bot.mvp_list = [Mvp(**dict(db_mvp)) for db_mvp in await conn.fetch('SELECT * FROM mvp')]
    for db_mvp_alias in await conn.fetch('SELECT * FROM mvp_alias'):
        mvp = next(x for x in bot.mvp_list if x.id == db_mvp_alias['id_mvp'])
        mvp.alias.append(db_mvp_alias['alias'])

    log.info('Load mining locations.')
    bot.mining_list = []
    for db_mining in await conn.fetch('SELECT * FROM mining'):
        mining = MiningLocation(**dict(db_mining))
        mining.t1 = 30
        bot.mining_list.append(mining)

    log.info('Load MVP entries.')
    await entry_service.load_db_entries(bot, conn, TrackType.MVP)

    log.info('Load mining location entries.')
    await entry_service.load_db_entries(bot, conn, TrackType.MINING)

    log.info('Init track channels.')
    for id_guild, guild_state in bot.guild_states.items():
        guild = channel_service.get_guild_from_bot(bot, id_guild)
        if guild is None:
            continue
        for channel_state in list(guild_state.channel_states.values()):
            await channel_service.init_channel(bot, channel_state)
    log.info('Track channels init done.')
