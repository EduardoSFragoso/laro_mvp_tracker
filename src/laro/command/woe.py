from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.domain.emoji import Emoji
from laro.service import event_service
from laro.util.coroutine_util import run_coro


async def woe_core(bot: Bot, message: discord.Message) -> None:
    woe_map = event_service.get_woe_map(bot)
    embed = event_service.build_evt_embed(bot, Emoji.WOE.value, 'WoE', woe_map)
    await run_coro(message.channel.send(embed=embed))
