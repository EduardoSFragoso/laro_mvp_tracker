from __future__ import annotations

import contextlib
import logging
import time
from datetime import UTC, datetime, timedelta

import discord

from laro.domain.bot import Bot
from laro.domain.models import ChannelState, EntryLog, GuildState, TrackEntryState
from laro.domain.track_type import TrackType
from laro.service import entry_service
from laro.util import track_util
from laro.util.coroutine_util import run_coro
from laro.util.date_util import get_dt_now, get_local_tzinfo
from laro.util.interaction_util import is_confirmation_owner_admin


log = logging.getLogger(__name__)

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


def parse_user_time(timezone: str, user_time: str) -> datetime | str:
    """Convert an ``HHMM`` user time to a datetime in the (recent) past in the
    given timezone. Returns an error message when the time is invalid."""
    if not (user_time.isnumeric() and len(user_time) == 4):
        return 'HHMM format expected for user time'
    hh = int(user_time[0:2])
    mm = int(user_time[2:4])
    if hh > 23:
        return 'HH must be between 00 and 23'
    if mm > 59:
        return 'MM must be between 00 and 59'
    track_time = get_dt_now(timezone)
    if hh > track_time.hour or (hh == track_time.hour and mm > track_time.minute):
        track_time -= timedelta(days=1)
    return track_time.replace(hour=hh, minute=mm)


def _resolve_query(
    bot: Bot, guild_state, channel_state: ChannelState, mvp: str, user_time: str | None
) -> tuple[list, int, str | None]:
    """Resolve ``mvp``/``user_time`` into (results, mins_ago, error)."""
    mins_ago = 0
    if user_time is not None:
        timezone = guild_state.timezone or bot.settings.timezone
        parsed = parse_user_time(timezone, user_time)
        if isinstance(parsed, str):
            return [], 0, parsed
        mins_ago = int((get_dt_now(timezone) - parsed) / timedelta(minutes=1))
    results = entry_service.find_entry(bot, mvp)
    return results, mins_ago, None


# --------------------------------------------------------------------------
# Tracking entry points
# --------------------------------------------------------------------------


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
    results: list,
    mins_ago: int,
    user_time: str | None,
    id_user: int,
    mvp: str,
    sender,
) -> None:
    type = channel_state.type
    if len(results) == 0:
        await run_coro(sender.send(f'{type.desc} "{mvp}" not found.'))
    elif len(results) == 1:
        bot_reply_msg = await update_track_time(
            bot, guild_state, channel_state, results[0], mins_ago, user_time, id_user
        )
        await run_coro(sender.send(bot_reply_msg))
    else:
        msg = _multiple_matches_msg(type, mvp, user_time)
        await run_coro(
            sender.send(
                msg,
                view=TrackView(bot=bot, opts=results, mins_ago=mins_ago, user_time=user_time),
            )
        )


def _multiple_matches_msg(type: TrackType, query: str, user_time: str | None) -> str:
    msg = 'More than one ' + type.desc
    msg += ' starting with "' + query + '" has been found.\n'
    msg += '\n'
    msg += 'Select the ' + type.desc + ' that you want to track'
    if user_time is not None:
        msg += ' with time ' + user_time
    msg += ':'
    return msg


class MessageSender:
    """Uniform send target around a text channel."""

    def __init__(self, channel: discord.abc.Messageable):
        self.channel = channel

    async def send(self, content: str, **kwargs):
        return await self.channel.send(content, **kwargs)


class InteractionSender:
    """Uniform send target around an interaction."""

    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction

    async def send(self, content: str, **kwargs):
        return await self.interaction.response.send_message(content, **kwargs)


# --------------------------------------------------------------------------
# Track update
# --------------------------------------------------------------------------


async def update_track_time(
    bot: Bot,
    guild_state: GuildState,
    channel_state: ChannelState,
    entry,
    mins_ago: int,
    user_time: str | None,
    id_user: int,
) -> str:
    type = channel_state.type
    row_sql = type.sql_desc
    date = datetime.now()
    track_time = date - timedelta(minutes=mins_ago)
    conn = await bot.pool_acquire()
    try:
        read_sql = f'SELECT * FROM {row_sql}_guild WHERE id_{row_sql}=$1 AND id_guild=$2'
        entry_guild_db = await conn.fetch(read_sql, entry.id, channel_state.id_guild)
        write_sql = f'INSERT INTO {row_sql}_guild(id_{row_sql},id_guild,track_time)VALUES($1,$2,$3)'
        if len(entry_guild_db) > 0:
            # Re-rastrear zera notified (novo ciclo de respawn) no banco também.
            write_sql = (
                f'UPDATE {row_sql}_guild SET track_time=$3, notified=FALSE WHERE id_{row_sql}=$1 AND id_guild=$2'
            )
        await conn.execute(write_sql, entry.id, channel_state.id_guild, track_time)

        read_sql = f'SELECT * FROM {row_sql}_guild_log WHERE id_{row_sql}=$1 AND id_guild=$2'
        entry_guild_log_db = await conn.fetch(read_sql, entry.id, channel_state.id_guild)
        write_sql = f'INSERT INTO {row_sql}_guild_log(id_{row_sql},id_guild,date,id_user)VALUES($1,$2,$3,$4)'
        if len(entry_guild_log_db) > 0:
            write_sql = f'UPDATE {row_sql}_guild_log SET date=$3,id_user=$4 WHERE id_{row_sql}=$1 AND id_guild=$2'
        await conn.execute(write_sql, entry.id, channel_state.id_guild, date, id_user)

        entry_log = next(
            (x for x in channel_state.entry_logs if x.entry is entry),
            None,
        )
        if entry_log is not None:
            channel_state.entry_logs.remove(entry_log)
        channel_state.entry_logs.appendleft(EntryLog(entry=entry, date=date, id_user=id_user))
        while len(channel_state.entry_logs) > 3:
            removed_log = channel_state.entry_logs.pop()
            del_sql = f'DELETE FROM {row_sql}_guild_log WHERE id_{row_sql}=$1 AND id_guild=$2'
            await conn.execute(del_sql, removed_log.entry.id, channel_state.id_guild)
    finally:
        await bot.pool_release(conn)

    entry_state = track_util.track_entry(channel_state, entry, track_time, custom=guild_state.custom)
    await update_channel_message(bot, channel_state)
    return _fmt_track_reply(entry_state, user_time)


def _fmt_track_reply(entry_state, user_time: str | None) -> str:
    msg = entry_state.entry.name
    msg += ' (' + entry_state.entry.display_map + ')'
    msg += ' in '
    msg += track_util.fmt_r1_r2(int(entry_state.r1))
    msg += ' to '
    msg += track_util.fmt_r1_r2(int(entry_state.r2))
    msg += ' minutes'
    if user_time is not None:
        msg += ' (time: ' + user_time + ')'
    msg += '.'
    return msg


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
    with contextlib.suppress(discord.DiscordException):
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
                try:
                    await run_coro(msg.delete())
                except discord.DiscordException:
                    log.error('Unexpected error deleting duplicate notification message.', exc_info=True)
        if help_msg is not None and table_msg is not None:
            break
    if table_msg is not None and (help_msg is None or help_msg.created_at > table_msg.created_at):
        # Table exists but the help message is missing or came after it:
        # remove the table and send help first, then a fresh table.
        try:
            await run_coro(table_msg.delete())
        except discord.DiscordException:
            log.error('Unexpected error deleting out-of-order table message.', exc_info=True)
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


# --------------------------------------------------------------------------
# UI components (views/buttons/selects/modals)
# --------------------------------------------------------------------------


class SetChannelView(discord.ui.View):
    def __init__(self, *, timeout=180, bot: Bot, trackType: TrackType, requester_id: int):
        super().__init__(timeout=timeout)
        self.requester_id = requester_id
        self.add_item(SetChannelYesButton(bot=bot, trackType=trackType))
        self.add_item(SetChannelNoButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await is_confirmation_owner_admin(interaction, self.requester_id)


class SetChannelYesButton(discord.ui.Button):
    def __init__(self, bot: Bot, trackType: TrackType):
        self.bot = bot
        self.trackType = trackType
        super().__init__(style=discord.ButtonStyle.primary, label='Yes')

    async def callback(self, interaction: discord.Interaction):
        await run_coro(interaction.response.edit_message(view=None))
        channel = interaction.channel
        if isinstance(channel, discord.TextChannel):
            await set_channel(self.bot, channel, self.trackType)


class SetChannelNoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label='No')

    async def callback(self, interaction: discord.Interaction):
        await run_coro(interaction.response.edit_message(view=None))


class TrackView(discord.ui.View):
    def __init__(self, *, timeout=180, bot: Bot, opts: list, mins_ago: int, user_time: str | None):
        super().__init__(timeout=timeout)
        self.add_item(TrackSelect(bot=bot, opts=opts, mins_ago=mins_ago, user_time=user_time))


class TrackSelect(discord.ui.Select):
    def __init__(self, bot: Bot, opts: list, mins_ago: int, user_time: str | None):
        self.bot = bot
        self.opts = opts
        self.mins_ago = mins_ago
        self.user_time = user_time
        options = [
            discord.SelectOption(label=opt.name, description=opt.display_map, value=str(opt.id)) for opt in self.opts
        ]
        super().__init__(placeholder='Select an option', options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild_id is None or interaction.channel_id is None:
            return
        entry = next((x for x in self.opts if str(x.id) == self.values[0]), None)
        guild_state = self.bot.get_guild_state(interaction.guild_id)
        if guild_state is None or entry is None:
            return
        channel_state = guild_state.channel_states.get(interaction.channel_id)
        if channel_state is None:
            return
        bot_reply_msg = await update_track_time(
            self.bot, guild_state, channel_state, entry, self.mins_ago, self.user_time, interaction.user.id
        )
        await run_coro(interaction.response.edit_message(content=bot_reply_msg, view=None))


class ChannelMessageView(discord.ui.View):
    def __init__(self, *, timeout=None, bot: Bot, channel_state: ChannelState):
        super().__init__(timeout=timeout)
        self.add_item(ChannelMessageTrackButton(bot=bot, channel_state=channel_state))


class ChannelMessageTrackButton(discord.ui.Button):
    def __init__(self, bot: Bot, channel_state: ChannelState):
        self.bot = bot
        self.channel_state = channel_state
        super().__init__(style=discord.ButtonStyle.primary, emoji='➕', label=f'TRACK {channel_state.type.desc}')

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ChannelMessageTrackModal(bot=self.bot, channel_state=self.channel_state))


class ChannelMessageTrackModal(discord.ui.Modal):
    def __init__(self, bot: Bot, channel_state: ChannelState):
        super().__init__(title=f'TRACK {channel_state.type.desc}')
        self.bot = bot
        self.channel_state = channel_state
        self.name_input = discord.ui.TextInput(label='Name')
        self.time_input = discord.ui.TextInput(label='Time', required=False)
        self.add_item(self.name_input)
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.strip()
        if len(name) > 0:
            user_time = self.time_input.value.strip()
            if len(user_time) == 0:
                user_time = None
            await track_by_interaction(self.bot, interaction, self.channel_state, name, user_time)
