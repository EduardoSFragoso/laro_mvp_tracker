from __future__ import annotations

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.emoji import Emoji
from yellowtracker.domain.track_type import TrackType
from yellowtracker.service import channel_service
from yellowtracker.util.coroutine_util import run_coro


async def settings_core(bot: Bot, message: discord.Message) -> None:
    guild = message.guild
    if guild is None:
        return
    guild_state = bot.get_guild_state(guild.id)
    if guild_state is None:
        return
    mvp_channel_state = guild_state.get_channel_state(TrackType.MVP)
    mvp_channel = (
        channel_service.get_channel_from_guild(guild, mvp_channel_state.id_channel)
        if mvp_channel_state is not None
        else None
    )
    notification_role = None
    if guild_state.id_notification_role is not None:
        notification_role = guild.get_role(guild_state.id_notification_role)
    msg = f'Custom MVP Times: {Emoji.YES.value if guild_state.custom else Emoji.NO.value}\n'
    msg += f'Mobile Layout: {Emoji.YES.value if guild_state.mobile else Emoji.NO.value}\n'
    msg += f'MVP Channel: {"" if mvp_channel is None else mvp_channel.mention}\n'
    msg += f'Notification Role: {"" if notification_role is None else notification_role.mention}\n'
    msg += f'Timezone: {"" if guild_state.timezone is None else guild_state.timezone}'
    await run_coro(message.channel.send(msg))
