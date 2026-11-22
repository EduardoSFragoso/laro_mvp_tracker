from __future__ import annotations

import discord
from yellowtracker.domain.bot import Bot
from yellowtracker.domain.track_type import TrackType
from yellowtracker.service import channel_service


async def unsetminingchannel(interaction: discord.Interaction, bot: Bot) -> None:
    await channel_service.unset_channel(bot, interaction, TrackType.MINING)
