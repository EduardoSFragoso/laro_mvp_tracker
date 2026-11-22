from __future__ import annotations

import logging

import discord

from yellowtracker.command import clean, settings, timezone, unset_mvp_channel, unsettimezone, woe
from yellowtracker.command.set_mvp_channel import setmvpchannel_core
from yellowtracker.command.track import track_core
from yellowtracker.domain.bot import Bot
from yellowtracker.service import channel_service


log = logging.getLogger(__name__)


async def on_message(bot: Bot, message: discord.Message) -> None:
    if bot.user.id == message.author.id:
        return

    if (
        isinstance(message.channel, discord.channel.TextChannel)
        and message.content.startswith(bot.settings.command_prefix)
        and bot.tracker_ready
    ):
        await _dispatch_cmd(bot, message)

    if not _is_dm_channel_message(bot, message):
        return

    args = message.content.split(' ', 1)
    if args[0] == '!guilds':
        await _guilds(bot, message.channel)
    if args[0] == '!notify':
        if len(args) < 2:
            return
        await _notify(bot, message.channel, args[1])
    if args[0] == '!sync':
        await _sync(bot, message.channel)
    if args[0] == '!channels':
        await _channels(bot, message.channel)


async def _dispatch_cmd(bot: Bot, message: discord.Message) -> None:
    prefix = bot.settings.command_prefix
    parts = message.content[len(prefix) :].strip().split()
    if len(parts) == 0:
        await _reply_help(bot, message)
        return
    sub = parts[0].lower()
    args = parts[1:]
    if sub == 'help':
        await _reply_help(bot, message)
    elif sub == 'track':
        await _cmd_track(bot, message, prefix, args)
    elif sub == 'woe':
        await woe.woe_core(bot, message)
    elif sub == 'settings':
        await settings.settings_core(bot, message)
    elif sub == 'clean':
        await clean.clean_core(bot, message)
    elif sub == 'timezone':
        if len(args) >= 1:
            await timezone.timezone_core(bot, message, ' '.join(args))
        else:
            await message.channel.send('Use: `' + prefix + ' timezone <timezone>`')
    elif sub == 'unsettimezone':
        await unsettimezone.unsettimezone_core(bot, message)
    elif sub == 'setmvpchannel':
        await setmvpchannel_core(bot, message)
    elif sub == 'unsetmvpchannel':
        await unset_mvp_channel.unsetmvpchannel_core(bot, message)
    else:
        # Com um prefixo curto (ex.: '!'), mensagens de outros bots/usuarios que
        # coincidam nao devem gerar ruido: sinaliza desconhecido so no canal de track.
        guild_state = bot.get_guild_state(message.guild.id)
        if guild_state is not None and guild_state.channel_states.get(message.channel.id) is not None:
            await message.channel.send(
                'Comando "' + sub + '" não existe. Digite `' + prefix + '` ou `' + prefix + ' help` '
                'para ver os comandos disponíveis.'
            )


async def _cmd_track(bot: Bot, message: discord.Message, prefix: str, args: list[str]) -> None:
    mvp, user_time = _split_track_args(args)
    if mvp is None:
        await message.channel.send('Use: `' + prefix + 'track <nome do MVP> [HHMM]`')
        return
    await track_core(bot, message, mvp, user_time)


def _split_track_args(args: list[str]) -> tuple[str | None, str | None]:
    if len(args) == 0:
        return None, None
    last = args[-1]
    hhmm = last.replace(':', '')
    if len(args) > 1 and hhmm.isnumeric() and len(hhmm) == 4:
        return ' '.join(args[:-1]), hhmm
    return ' '.join(args), None


async def _reply_help(bot: Bot, message: discord.Message) -> None:
    from yellowtracker.service.channel_service import get_help_description

    embed = discord.Embed(
        colour=discord.Colour.gold(),
        title=':book: Comandos',
        description=get_help_description(bot.settings.command_prefix),
    )
    await message.channel.send(embed=embed)


async def _guilds(bot: Bot, dm_channel: discord.abc.Messageable) -> None:
    lines = []
    for guild in bot.guilds:
        owner = None
        if guild.owner_id is not None:
            owner = await guild.fetch_member(guild.owner_id)
        lines.append(f'{guild.name} | {owner} | {guild.id}')
    await _send_paginated(bot, dm_channel, 'Guilds', 'Name | Owner | ID', lines)


async def _notify(bot: Bot, dm_channel: discord.abc.Messageable, user_msg: str) -> None:
    users_id = {guild.owner_id for guild in bot.guilds}
    count = 0
    for user_id in users_id:
        user = await bot.fetch_user(user_id)
        if user is not None:
            msg = 'You are receiving this message because you own a discord server that have this bot.'
            msg += '\n\n'
            msg += user_msg
            await user.send(msg)
            count += 1
    await dm_channel.send(f'Notification sent to {count} users.')


async def _sync(bot: Bot, dm_channel: discord.abc.Messageable) -> None:
    await dm_channel.send('Slash commands are no longer used (commands are prefix-based).')


async def _channels(bot: Bot, dm_channel: discord.abc.Messageable) -> None:
    lines = []
    for guild in bot.guilds:
        guild_state = bot.get_guild_state(guild.id)
        if guild_state is None:
            continue
        for channel_state in list(guild_state.channel_states.values()):
            if len(channel_state.entry_states) == 0:
                continue
            owner = None
            if guild.owner_id is not None:
                owner = await guild.fetch_member(guild.owner_id)
            if owner is None:
                continue
            channel = channel_service.get_channel_from_guild(guild, channel_state.id_channel)
            if channel is None:
                continue
            line = f'{channel} | '
            line += f'{channel_state.type.sql_desc} | '
            line += f'{guild} | '
            line += f'{owner} | '
            line += f'{guild_state.timezone if guild_state.timezone is not None else "-"} | '
            line += f'{"Yes" if guild_state.custom else "No"} | '
            line += f'{"Yes" if guild_state.mobile else "No"} | '
            line += f'{len(channel_state.entry_states)}'
            lines.append(line)
    header = 'Channel | Type | Guild | Owner | Timezone | Custom | Mobile | Entries'
    await _send_paginated(bot, dm_channel, 'Channels', header, lines)


async def _send_paginated(
    bot: Bot, dm_channel: discord.abc.Messageable, title: str, header: str, lines: list[str]
) -> None:
    page_size = 10
    if len(lines) == 0:
        embed = discord.Embed(color=discord.Colour.gold(), title=title)
        embed.add_field(name=header, value='Empty', inline=False)
        await dm_channel.send(embed=embed)
        return
    offset = 1
    count = 0
    msg = ''
    for line in lines:
        msg += f'{line}\n'
        count += 1
        if count == page_size:
            embed = discord.Embed(color=discord.Colour.gold(), title=title)
            embed.add_field(name=header, value=msg, inline=False)
            embed.set_footer(text=f'{offset} to {offset + count - 1} (Total: {len(lines)})')
            await dm_channel.send(embed=embed)
            msg = ''
            offset = offset + count
            count = 0
    if count > 0:
        embed = discord.Embed(color=discord.Colour.gold(), title=title)
        embed.add_field(name=header, value=msg, inline=False)
        embed.set_footer(text=f'{offset} to {offset + count - 1} (Total: {len(lines)})')
        await dm_channel.send(embed=embed)


def _is_dm_channel_message(bot: Bot, message: discord.Message) -> bool:
    if not message.content.startswith('!'):
        return False
    if not isinstance(message.channel, discord.DMChannel):
        return False
    if bot.application is None:
        return False
    bot_owner = bot.application.owner
    if bot_owner is None:
        return False
    return bot_owner.id == message.author.id
