from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.domain.track_type import TrackType
from laro.service import channel_service


async def setmvpchannel_core(bot: Bot, message: discord.Message) -> None:
    if not isinstance(message.channel, discord.TextChannel):
        return
    await channel_service.confirm_set_channel(bot, message.channel, TrackType.MVP)
