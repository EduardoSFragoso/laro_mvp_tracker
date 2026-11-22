from __future__ import annotations

import discord
from yellowtracker.domain.bot import Bot
from yellowtracker.domain.emoji import Emoji
from yellowtracker.service import event_service
from yellowtracker.util.coroutine_util import run_coro
from yellowtracker.util.date_util import fmt_dt, get_dt_now


async def gmc(interaction: discord.Interaction, bot: Bot) -> None:
    gmc_map = event_service.get_gmc_map(bot)
    embed = discord.Embed()
    embed.title = f'{Emoji.GMC.value} GMC'
    embed.colour = discord.Colour.gold()
    if gmc_map['ongoing'] != '':
        embed.add_field(name='Ongoing :boom:', value=gmc_map['ongoing'], inline=False)
    embed.add_field(name='Next :arrow_right:', value=gmc_map['next'], inline=False)
    if gmc_map['today'] != '':
        embed.add_field(name='Today', value=gmc_map['today'], inline=False)
    if gmc_map['tomorrow'] != '':
        embed.add_field(name='Tomorrow', value=gmc_map['tomorrow'], inline=False)
    footer = 'Server Time (' + bot.settings.timezone + '): '
    footer += fmt_dt(get_dt_now(bot.settings.timezone))
    embed.set_footer(text=footer)
    await run_coro(interaction.response.send_message(embed=embed, view=GmcView(bot)))


class GmcView(discord.ui.View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(GmcTokensButton(bot=bot))


class GmcTokensButton(discord.ui.Button):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__(style=discord.ButtonStyle.primary, emoji='🗒️', label='Manage GMC Tokens')

    async def callback(self, interaction: discord.Interaction):
        from yellowtracker.command import gmctokens  # local import avoids a circular dependency
        gmcTokenUser = gmctokens.GmcTokenUser(self.bot, interaction.user)
        await gmcTokenUser.initAccs()
        await interaction.response.send_message(
            ephemeral=True, embed=gmcTokenUser.embed(), view=gmctokens.GmcTokensView(gmcTokenUser=gmcTokenUser))
