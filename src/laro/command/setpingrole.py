from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.util.coroutine_util import run_coro


async def setpingrole_core(bot: Bot, message: discord.Message) -> None:
    guild = message.guild
    if guild is None:
        return
    guild_state = bot.get_guild_state(guild.id)
    if guild_state is None:
        return
    prefix = bot.settings.command_prefix
    role = None
    if len(message.role_mentions) >= 1:
        role = message.role_mentions[0]
    else:
        parts = message.content.strip().split()
        if len(parts) >= 2 and parts[1].isnumeric():
            role = guild.get_role(int(parts[1]))
    if role is None:
        msg = 'Use: `' + prefix + 'setpingrole @role` (ou `' + prefix + 'setpingrole <id da role>`).'
        await run_coro(message.channel.send(msg))
        return
    guild_state.id_notification_role = role.id
    conn = await bot.pool_acquire()
    try:
        await conn.execute('UPDATE guild SET id_notification_role=$2 WHERE id=$1', guild.id, role.id)
    finally:
        await bot.pool_release(conn)
    msg = 'Role de notificação configurada: ' + role.mention + '.'
    msg += '\nQuando a janela de respawn de um MVP abrir, o bot vai pingar essa role no canal de track.'
    msg += '\nPara remover: `' + prefix + 'unsetpingrole` (aí não pinga ninguém).'
    await run_coro(message.channel.send(msg, allowed_mentions=discord.AllowedMentions.none()))


async def unsetpingrole_core(bot: Bot, message: discord.Message) -> None:
    guild = message.guild
    if guild is None:
        return
    guild_state = bot.get_guild_state(guild.id)
    if guild_state is None:
        return
    guild_state.id_notification_role = None
    conn = await bot.pool_acquire()
    try:
        await conn.execute('UPDATE guild SET id_notification_role=NULL WHERE id=$1', guild.id)
    finally:
        await bot.pool_release(conn)
    prefix = bot.settings.command_prefix
    msg = 'Role de notificação removida. Agora o aviso de janela de respawn não pinga ninguém.'
    msg += '\nPara configurar de novo: `' + prefix + 'setpingrole @role`.'
    await run_coro(message.channel.send(msg))
