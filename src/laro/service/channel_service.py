from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta

import discord

from laro.domain.bot import Bot
from laro.domain.models import ChannelState, TrackEntryState
from laro.domain.track_type import TrackType
from laro.service.tracking_service import (
    _multiple_matches_msg,
    _resolve_query,
    parse_user_time,
    track_by_interaction,
    track_by_message,
    update_track_time,
)
from laro.ui.channel_views import ChannelMessageView, SetChannelView
from laro.util import track_util
from laro.util.coroutine_util import run_coro
from laro.util.date_util import get_dt_now, get_local_tzinfo


log = logging.getLogger(__name__)

__all__ = [
    '_multiple_matches_msg',
    '_resolve_query',
    'parse_user_time',
    'track_by_interaction',
    'track_by_message',
    'update_track_time',
]

TABLE_MAX_ROWS = 20

HELP_EMBED_TITLE = ':book: Como usar'
NOTIFICATION_EMBED_TITLE = ':bell: Janelas de respawn abertas'


def get_guild_from_bot(bot: Bot, id_guild: int) -> discord.Guild | None:
    return next((x for x in bot.guilds if x.id == id_guild), None)


def get_channel_from_guild(guild: discord.Guild, id_channel: int) -> discord.TextChannel | None:
    return next((x for x in guild.text_channels if x.id == id_channel), None)


def get_channel_from_bot(bot: Bot, id_guild: int, id_channel: int) -> discord.TextChannel | None:
    guild = get_guild_from_bot(bot, id_guild)
    if guild is None:
        return None
    return get_channel_from_guild(guild, id_channel)


def validate_channel(bot: Bot, channel) -> str | None:
    """Return an error message when the bot cannot operate the channel."""
    if channel is None:
        return 'Invalid channel.'
    member = next((x for x in channel.members if x == bot.user), None)
    if member is None:
        return 'Bot need to be a member of this channel.'
    permissions = channel.permissions_for(member)
    missing = []
    if not permissions.read_messages:
        missing.append('Read Messages')
    if not permissions.send_messages:
        missing.append('Send Messages')
    if not permissions.manage_messages:
        missing.append('Manage Messages')
    if not permissions.read_message_history:
        missing.append('Read Message History')
    if not permissions.add_reactions:
        missing.append('Add Reactions')
    if len(missing) > 0:
        msg = 'Bot is missing the following permissions:\n\n'
        for idx in range(len(missing)):
            msg += str(idx + 1) + '. ' + missing[idx] + '\n'
        return msg
    return None


# --------------------------------------------------------------------------
# Window-open notification
# --------------------------------------------------------------------------


async def update_notification(
    bot: Bot, channel_state: ChannelState, open_entries: list, new_entries: list[TrackEntryState]
) -> None:
    """Keep a live notification message for MVPs whose respawn window is open.

    With no open window there is no message; when windows are open the message
    persists (heading the channel) until the last window closes. Only a brand
    new window pings the configured role — ongoing updates are silent edits.
    """
    channel = get_channel_from_bot(bot, channel_state.id_guild, channel_state.id_channel)
    if channel is None:
        return
    # No open window: remove the message if it still exists.
    if len(open_entries) == 0:
        if channel_state.notification_message is not None:
            await _delete_notification(channel_state)
        return
    new_windows = bool(new_entries)
    guild_state = bot.get_guild_state(channel_state.id_guild)
    if guild_state is None:
        return
    timezone = guild_state.timezone or bot.settings.timezone
    embed = _notification_embed(timezone, open_entries)
    msg = channel_state.notification_message
    if msg is None:
        content = None
        allowed_mentions = discord.AllowedMentions.none()
        role_id = guild_state.id_notification_role
        guild = get_guild_from_bot(bot, guild_state.id_guild)
        role = guild.get_role(role_id) if new_windows and role_id is not None and guild is not None else None
        if role is not None:
            content = role.mention
            allowed_mentions = discord.AllowedMentions(roles=[role])
        try:
            sent = await channel.send(content, embed=embed, allowed_mentions=allowed_mentions)
        except discord.DiscordException:
            log.error('Error sending notification message.', exc_info=True)
            return
        channel_state.notification_message = sent
    else:
        if not await _edit_notification(bot, channel_state, msg, embed, guild_state, role_ping=new_windows):
            return

    if new_entries:
        for entry_state in new_entries:
            entry_state.notified = True
            entry_state.notification_pending = False
        # Persiste após o envio/edição bem-sucedido, para não perder um aviso
        # quando o Discord rejeitar temporariamente a mensagem.
        conn = await bot.pool_acquire()
        try:
            sql = (
                f'UPDATE {channel_state.type.sql_desc}_guild '
                f'SET notified=TRUE WHERE id_{channel_state.type.sql_desc}=$1 AND id_guild=$2'
            )
            for entry_state in new_entries:
                await conn.execute(sql, entry_state.entry.id, channel_state.id_guild)
        finally:
            await bot.pool_release(conn)


def _notification_embed(timezone: str, open_entries: list) -> discord.Embed:
    now = get_dt_now(timezone)
    lines = []
    for entry_state in sorted(open_entries, key=lambda e: int(e.r2)):
        end = (now + timedelta(minutes=int(entry_state.r2))).strftime('%H:%M')
        lines.append(
            '- **' + entry_state.entry.name + '** (' + entry_state.entry.display_map + ') — janela aberta até ~' + end
        )
    return discord.Embed(colour=discord.Colour.gold(), title=NOTIFICATION_EMBED_TITLE, description='\n'.join(lines))


async def _edit_notification(
    bot: Bot, channel_state: ChannelState, msg: discord.Message, embed: discord.Embed, guild_state, role_ping: bool
) -> bool:
    # Skip the edit when nothing changed (the timer runs every minute).
    old_description = msg.embeds[0].description if len(msg.embeds) > 0 else None
    if old_description == embed.description and not role_ping:
        return True
    # A new window opening (role_ping) mentions the role again on the edit.
    content = None
    allowed_mentions = discord.AllowedMentions.none()
    if role_ping and guild_state.id_notification_role is not None:
        guild = get_guild_from_bot(bot, guild_state.id_guild)
        role = guild.get_role(guild_state.id_notification_role) if guild is not None else None
        if role is not None:
            content = role.mention
            allowed_mentions = discord.AllowedMentions(roles=[role])
    try:
        await msg.edit(content=content, embed=embed, allowed_mentions=allowed_mentions)
        return True
    except discord.DiscordException:
        # Message deleted by someone: drop the reference; the next tick sends a new one.
        channel_state.notification_message = None
        return False


async def _delete_notification(channel_state: ChannelState) -> None:
    msg = channel_state.notification_message
    if msg is None:
        return
    channel_state.notification_message = None
    await run_coro(msg.delete())


# --------------------------------------------------------------------------
# Channel lifecycle
# --------------------------------------------------------------------------


async def init_channel(bot: Bot, channel_state: ChannelState) -> None:
    channel = get_channel_from_bot(bot, channel_state.id_guild, channel_state.id_channel)
    if channel is None:
        return
    if validate_channel(bot, channel) is not None:
        return
    channel_state.id_message = None
    channel_state.id_help_message = None
    help_msg = None
    table_msg = None
    notification_msg = None
    async for msg in channel.history():
        if msg.type != discord.MessageType.default or msg.author != bot.user:
            continue
        embed_title = msg.embeds[0].title if len(msg.embeds) > 0 else None
        if embed_title == HELP_EMBED_TITLE and help_msg is None:
            help_msg = msg
        elif embed_title == ':crown: MVPs' and table_msg is None:
            table_msg = msg
        elif embed_title == NOTIFICATION_EMBED_TITLE:
            # Restart: adota o aviso mais recente; duplicados são apagados.
            if notification_msg is None:
                notification_msg = msg
            else:
                await run_coro(msg.delete())
        if help_msg is not None and table_msg is not None:
            break
    if table_msg is not None and (help_msg is None or help_msg.created_at > table_msg.created_at):
        # Table exists but the help message is missing or came after it:
        # remove the table and send help first, then a fresh table.
        await run_coro(table_msg.delete())
        table_msg = None
    if help_msg is None:
        await send_help_message(bot, channel_state)
    else:
        channel_state.id_help_message = help_msg.id
        await send_help_message(bot, channel_state, help_msg)
    if table_msg is not None:
        channel_state.id_message = table_msg.id
    channel_state.notification_message = notification_msg
    await update_channel_message(bot, channel_state)
    await delete_msgs(bot, channel_state, channel)
    # Depois da limpeza, um aviso adotado sem janelas abertas é removido.
    await _prune_notification(bot, channel_state)


async def _prune_notification(bot: Bot, channel_state: ChannelState) -> None:
    if channel_state.notification_message is None:
        return
    open_entries = [
        entry_state for entry_state in channel_state.entry_states if int(entry_state.r1) <= 0 <= int(entry_state.r2)
    ]
    if len(open_entries) == 0:
        await _delete_notification(channel_state)


def get_help_description(prefix: str) -> str:
    p = prefix
    return (
        'Adicione um MVP à lista usando o botão **➕ TRACK MVP** '
        'ou digitando no chat:\n'
        f'> `{p}track <nome> [horário da morte HHMM]`\n'
        '\n'
        '**Exemplos:**\n'
        f'> `{p}track Serpente Suprema` — sem horário = morreu agora\n'
        f'> `{p}track Serpente Suprema 20:35` — morreu às 20:35\n'
        f'> `{p}track` — mostra todos os comandos\n'
        '\n'
        '**Outros comandos:**\n'
        f'- `{p}settings` — tempos de spawn e timezone\n'
        f'- `{p}woe` — horários da WoE\n'
        f'- `{p}clean` — limpa o canal\n'
        f'- `{p}mobile` — alterna a lista entre layout normal e mobile\n'
        f'- `{p}setmvpchannel` / `{p}unsetmvpchannel` — canal de notificação\n'
        f'- `{p}setpingrole` / `{p}unsetpingrole` — role pingada no aviso de respawn\n'
        '\n'
        ':bell: Quando a janela de respawn de um MVP abrir, o bot avisa aqui '
        '(pingando a role cadastrada em `' + p + 'setpingrole`, se houver); '
        'o aviso fica no canal até a última janela fechar.\n'
        '\n'
        f':warning: Só mensagens que começam com `{p}` são processadas. '
        'As demais são apagadas automaticamente.'
    )


def _help_embed(bot: Bot) -> discord.Embed:
    return discord.Embed(
        colour=discord.Colour.gold(),
        title=HELP_EMBED_TITLE,
        description=get_help_description(bot.settings.command_prefix),
    )


async def send_help_message(bot: Bot, channel_state: ChannelState, message: discord.Message | None = None) -> None:
    channel = get_channel_from_bot(bot, channel_state.id_guild, channel_state.id_channel)
    if channel is None:
        return
    if validate_channel(bot, channel) is not None:
        return
    # When a help message already exists (restart), refresh its content instead
    # of sending a duplicate; otherwise send a new one after the welcome spot.
    if message is not None:
        await run_coro(message.edit(embed=_help_embed(bot)))
        return
    sent = await run_coro(channel.send(embed=_help_embed(bot)))
    if sent is not None:
        channel_state.id_help_message = sent.id


async def delete_msgs(bot: Bot, channel_state: ChannelState, channel: discord.TextChannel) -> None:
    msgs_to_delete = []
    async for msg in channel.history():
        if is_msg_can_be_deleted(bot, channel_state, msg):
            msgs_to_delete.append(msg)
    if len(msgs_to_delete) > 0:
        await run_coro(channel.delete_messages(msgs_to_delete))


def is_msg_can_be_deleted(bot: Bot, channel_state: ChannelState, msg: discord.Message) -> bool:
    if channel_state.id_message is not None and channel_state.id_message == msg.id:
        return False
    if channel_state.id_help_message is not None and channel_state.id_help_message == msg.id:
        return False
    # O aviso de janela de respawn é gerenciado pelo timer (some quando a
    # última janela fecha); a rotina de limpeza não pode apagá-lo antes.
    if channel_state.notification_message is not None and channel_state.notification_message.id == msg.id:
        return False
    # msg.created_at/edited_at são tz-aware (UTC); utcnow() deprecado não entra.
    if datetime.now(UTC) - msg.created_at >= timedelta(days=14):
        return False
    msg_date = msg.created_at if msg.edited_at is None else msg.edited_at
    return datetime.now(UTC) - msg_date > timedelta(seconds=bot.settings.del_msg_after_secs)


async def set_channel(bot: Bot, channel: discord.TextChannel, type: TrackType) -> None:
    guild_state = bot.guild_states[channel.guild.id]
    channel_state = guild_state.remove_channel_state(type)
    entry_states = channel_state.entry_states if channel_state is not None else []
    channel_state = ChannelState(
        id_channel=channel.id,
        id_guild=channel.guild.id,
        type=type,
        entry_states=entry_states,
    )
    guild_state.channel_states[channel.id] = channel_state
    await init_channel(bot, channel_state)
    if channel_state.id_message is None:
        await send_help_message(bot, channel_state)
    await update_channel_message(bot, channel_state)
    conn = await bot.pool_acquire()
    try:
        sql = f'UPDATE guild SET id_{type.sql_desc}_channel=$1 WHERE id=$2'
        await conn.execute(sql, channel.id, channel.guild.id)
    finally:
        await bot.pool_release(conn)


async def unset_channel(bot: Bot, channel: discord.TextChannel, trackType: TrackType) -> None:
    validate_msg = validate_channel(bot, channel)
    if validate_msg is not None:
        await run_coro(channel.send(validate_msg))
        return
    guild_state = bot.guild_states[channel.guild.id]
    channel_state = guild_state.get_channel_state(trackType)
    if channel_state is None:
        await run_coro(channel.send(f'There is no {trackType.desc} channel set.'))
        return
    del guild_state.channel_states[channel_state.id_channel]
    conn = await bot.pool_acquire()
    try:
        sql = f'UPDATE guild SET id_{trackType.sql_desc}_channel=NULL WHERE id=$1'
        await conn.execute(sql, channel.guild.id)
    finally:
        await bot.pool_release(conn)
    await run_coro(channel.send(trackType.desc + ' channel unset.'))


async def confirm_set_channel(bot: Bot, channel: discord.TextChannel, trackType: TrackType, requester_id: int) -> None:
    validate_msg = validate_channel(bot, channel)
    if validate_msg is not None:
        await run_coro(channel.send(validate_msg))
        return
    await run_coro(
        channel.send(
            'This will remove all messages from this channel. Are you sure?',
            view=SetChannelView(bot=bot, trackType=trackType, requester_id=requester_id),
        )
    )


# --------------------------------------------------------------------------
# Track table message
# --------------------------------------------------------------------------


async def update_channel_message(bot: Bot, channel_state: ChannelState) -> None:
    local_tz = get_local_tzinfo()
    guild_state = bot.guild_states[channel_state.id_guild]
    mobile = guild_state.mobile

    embed = discord.Embed()
    embed.colour = discord.Colour.gold()
    embed.title = ':crown: MVPs'

    names: list[str] = []
    maps: list[str] = []
    remaining_times: list[str] = []
    id_mob_first_entry = None

    active_entry_states = []
    inactive_entry_state_ids = []
    for entry_state in channel_state.entry_states:
        if entry_state.r2 > -bot.settings.table_entry_expiration_mins:
            remaining_time = track_util.fmt_r1_r2(int(entry_state.r1))
            if id_mob_first_entry is None:
                id_mob_first_entry = entry_state.entry.id_mob
            remaining_time += ' to ' + track_util.fmt_r1_r2(int(entry_state.r2))
            remaining_time += ' mins'
            if mobile:
                names.append(
                    entry_state.entry.name + ' (' + entry_state.entry.display_map + ')' + ' | ' + remaining_time
                )
            else:
                names.append(entry_state.entry.name)
                maps.append(entry_state.entry.display_map)
                remaining_times.append(remaining_time)
            active_entry_states.append(entry_state)
        else:
            inactive_entry_state_ids.append((entry_state.entry.id, channel_state.id_guild))

    channel_state.entry_states = active_entry_states

    conn = await bot.pool_acquire()
    try:
        del_entry_state_sql = 'DELETE FROM mvp_guild WHERE id_mvp=$1 AND id_guild=$2'
        await conn.executemany(del_entry_state_sql, inactive_entry_state_ids)
    finally:
        await bot.pool_release(conn)

    if len(names) == 0:
        embed.add_field(name=':x:', value='MVP list is empty', inline=False)
    else:
        if len(names) > TABLE_MAX_ROWS + 1:
            diff = len(names) - TABLE_MAX_ROWS
            for _ in range(0, diff):
                names.pop()
                maps.pop()
                remaining_times.pop()
            names.append(f'and {diff} more...')
        if id_mob_first_entry is not None:
            embed.set_thumbnail(url='https://file5s.ratemyserver.net/mobs/' + str(id_mob_first_entry) + '.gif')
        if mobile:
            embed.add_field(name='Name', value=track_util.fmt_column(names), inline=False)
        else:
            embed.add_field(name='Name', value=track_util.fmt_column(names), inline=True)
            embed.add_field(name='Map', value=track_util.fmt_column(maps), inline=True)
            embed.add_field(name='Remaining Time', value=track_util.fmt_column(remaining_times), inline=True)

    if len(channel_state.entry_logs) > 0:
        result = ''
        for entry_log in channel_state.entry_logs:
            if result != '':
                result += '\n'
            result += f'[<t:{int(time.mktime(entry_log.date.astimezone(tz=local_tz).timetuple()))}:R>]'
            result += ' ' + entry_log.entry.name
            result += ' (' + entry_log.entry.display_map + ')'
            result += ' by <@' + str(entry_log.id_user) + '>'
        embed.add_field(name='Track Log', value=result, inline=False)

    guild = get_guild_from_bot(bot, channel_state.id_guild)
    if guild is None:
        return
    channel = get_channel_from_bot(bot, channel_state.id_guild, channel_state.id_channel)
    if channel is None:
        return
    if validate_channel(bot, channel) is not None:
        return
    message = None
    if channel_state.id_message is not None:
        try:
            message = await channel.fetch_message(channel_state.id_message)
        except discord.errors.NotFound:
            pass
        except discord.DiscordException:
            log.error('Unexpected error fetching track message.', exc_info=True)
            return
    view = ChannelMessageView(bot=bot, channel_state=channel_state)
    if message is None:
        message = await run_coro(channel.send(embed=embed, view=view))
        if message is not None:
            channel_state.id_message = message.id
    else:
        await run_coro(message.edit(embed=embed, view=view, content=''))
        await run_coro(message.clear_reactions())
