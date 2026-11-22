from __future__ import annotations

import discord

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.emoji import Emoji
from yellowtracker.service import event_service
from yellowtracker.util.coroutine_util import run_coro


async def gmc(interaction: discord.Interaction, bot: Bot) -> None:
    gmc_map = event_service.get_gmc_map(bot)
    embed = event_service.build_evt_embed(bot, Emoji.GMC.value, 'GMC', gmc_map)
    await run_coro(interaction.response.send_message(embed=embed))
