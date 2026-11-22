from __future__ import annotations

import discord
from yellowtracker.domain.bot import Bot
from yellowtracker.domain.emoji import Emoji
from yellowtracker.service import event_service
from yellowtracker.util.coroutine_util import run_coro
from yellowtracker.util.date_util import fmt_dt, get_dt_now


async def woe(interaction: discord.Interaction, bot: Bot) -> None:
    woe_map = event_service.get_woe_map(bot)
    embed = discord.Embed()
    embed.title = f'{Emoji.WOE.value} WoE'
    embed.colour = discord.Colour.gold()
    if woe_map['ongoing'] != '':
        embed.add_field(name='Ongoing :boom:', value=woe_map['ongoing'], inline=False)
    embed.add_field(name='Next :arrow_right:', value=woe_map['next'], inline=False)
    embed.add_field(name='Saturday', value=woe_map['saturday'], inline=False)
    embed.add_field(name='Sunday', value=woe_map['sunday'], inline=False)
    footer = 'Server Time (' + bot.settings.timezone + '): '
    footer += fmt_dt(get_dt_now(bot.settings.timezone))
    embed.set_footer(text=footer)
    await run_coro(interaction.response.send_message(embed=embed))
