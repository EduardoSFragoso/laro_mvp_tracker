from __future__ import annotations

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.track_type import TrackType
from yellowtracker.service import channel_service


async def unsetmvpchannel_core(bot: Bot, message: discord.Message) -> None:
    await channel_service.unset_channel(bot, message.channel, TrackType.MVP)
