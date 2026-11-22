from __future__ import annotations

import discord
from yellowtracker.domain.bot import Bot
from yellowtracker.domain.emoji import Emoji
from yellowtracker.service import event_service
from yellowtracker.util.coroutine_util import run_coro
from yellowtracker.util.date_util import fmt_dt, get_dt_now


async def hh(interaction: discord.Interaction, bot: Bot) -> None:
    bghh_map = event_service.get_hh_map(bot)
    embed = discord.Embed()
    embed.title = f'{Emoji.HH.value} BG Happy Hour'
    embed.colour = discord.Colour.gold()
    if bghh_map['ongoing'] != '':
        embed.add_field(name='Ongoing :boom:', value=bghh_map['ongoing'], inline=False)
    embed.add_field(name='Next :arrow_right:', value=bghh_map['next'], inline=False)
    if bghh_map['today'] != '':
        embed.add_field(name='Today', value=bghh_map['today'], inline=False)
    if bghh_map['tomorrow'] != '':
        embed.add_field(name='Tomorrow', value=bghh_map['tomorrow'], inline=False)
    footer = 'Server Time (' + bot.settings.timezone + '): '
    footer += fmt_dt(get_dt_now(bot.settings.timezone))
    embed.set_footer(text=footer)
    await run_coro(interaction.response.send_message(embed=embed))
