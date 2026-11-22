from __future__ import annotations

import discord
from yellowtracker.domain.bot import Bot
from yellowtracker.domain.emoji import Emoji
from yellowtracker.domain.track_type import TrackType
from yellowtracker.service import channel_service
from yellowtracker.util.coroutine_util import run_coro


async def settings_cmd(interaction: discord.Interaction, bot: Bot) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.defer()
        return
    guild_state = bot.guild_states[guild.id]
    mvp_channel = guild_state.get_channel_state(TrackType.MVP)
    mvp_channel = channel_service.get_channel_from_guild(guild, mvp_channel.id_channel) if mvp_channel is not None else None
    msg = f"Custom MVP Times: {Emoji.YES.value if guild_state.custom else Emoji.NO.value}\n"
    msg += f"Mobile Layout: {Emoji.YES.value if guild_state.mobile else Emoji.NO.value}\n"
    msg += f"MVP Channel: {'' if mvp_channel is None else mvp_channel.mention}\n"
    msg += f"Timezone: {'' if guild_state.timezone is None else guild_state.timezone}"
    await run_coro(interaction.response.send_message(msg))
