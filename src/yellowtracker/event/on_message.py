from __future__ import annotations

import logging
import time

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.models import ChannelState
from yellowtracker.service import channel_service


log = logging.getLogger(__name__)


async def on_message(bot: Bot, tree: discord.app_commands.CommandTree, message: discord.Message) -> None:
    if bot.user.id == message.author.id:
        return

    if isinstance(message.channel, discord.channel.TextChannel):
        guild_state = bot.get_guild_state(message.guild.id)
        if not guild_state:
            return
        channel_state = guild_state.channel_states.get(message.channel.id)
        if not channel_state:
            return
        await _track(bot, message, channel_state)

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
        await _sync(bot, tree, message.channel)
    if args[0] == '!channels':
        await _channels(bot, message.channel)


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


async def _sync(bot: Bot, tree: discord.app_commands.CommandTree, dm_channel: discord.abc.Messageable) -> None:
    ts = time.time()
    await dm_channel.send(f'Begin sync slash commands with {len(bot.guilds)} guilds.')
    for guild in bot.guilds:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
    await dm_channel.send(f'Slash commands synced with {len(bot.guilds)} guilds in {int(time.time() - ts)} secs.')


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


async def _track(bot: Bot, message: discord.Message, channel_state: ChannelState) -> None:
    mvp = _get_mvp(message.content)
    user_time = _get_user_time(message.content)
    await channel_service.track_by_message(bot, message, channel_state, mvp, user_time)


def _get_mvp(msg: str) -> str:
    parts = msg.split(' ')
    if len(parts) > 1:
        last = parts[1]
        if last.isnumeric() and len(last) == 4:
            return parts[0]
    return msg


def _get_user_time(msg: str) -> str | None:
    parts = msg.split(' ')
    if len(parts) > 1:
        last = parts[1]
        if last.isnumeric() and len(last) == 4:
            return parts[1]
    return None
