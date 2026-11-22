from __future__ import annotations

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.emoji import Emoji
from yellowtracker.service import event_service
from yellowtracker.util.coroutine_util import run_coro


async def hh(interaction: discord.Interaction, bot: Bot) -> None:
    hh_map = event_service.get_hh_map(bot)
    embed = event_service.build_evt_embed(bot, Emoji.HH.value, 'BG Happy Hour', hh_map)
    await run_coro(interaction.response.send_message(embed=embed))
