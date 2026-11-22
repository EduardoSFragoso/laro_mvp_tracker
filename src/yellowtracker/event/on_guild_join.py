from __future__ import annotations

import logging

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.models import GuildState

log = logging.getLogger(__name__)


async def on_guild_join(guild: discord.Guild, tree: discord.app_commands.CommandTree, bot: Bot) -> None:
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    log.info(f'Joined to {guild.name}.')
    bot.guild_states[guild.id] = GuildState(id_guild=guild.id)
    conn = await bot.pool_acquire()
    try:
        db_guild = await conn.fetch('SELECT * FROM guild WHERE id=$1', guild.id)
        if len(db_guild) == 0:
            await conn.execute('INSERT INTO guild(id)VALUES($1)', guild.id)
    finally:
        await bot.pool_release(conn)
