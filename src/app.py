from __future__ import annotations

import asyncio
import logging

import discord

from yellowtracker.command import clean, custom, gmc, hh, mobile, settings, set_mining_channel, \
    set_mvp_channel, timezone, track, unset_mining_channel, unset_mvp_channel, unsettimezone, woe
from yellowtracker.config import load_settings
from yellowtracker.domain.bot import Bot
from yellowtracker.event import on_guild_join, on_guild_remove, on_message, on_ready

log = logging.getLogger(__name__)

settings_cfg = load_settings()
discord.utils.setup_logging()

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(settings_cfg, intents=intents)
tree = discord.app_commands.CommandTree(bot)


@tree.command(name='clean', description='Remove all tracked MVPs from the list')
async def _clean(interaction: discord.Interaction):
    await clean.clean(interaction, bot)


@tree.command(name='custom', description='Enable/disable custom MVP respawn times')
async def _custom(interaction: discord.Interaction):
    await custom.custom_cmd(interaction, bot)


@tree.command(name='timezone', description='Define a custom timezone for MVP tracking')
async def _timezone(interaction: discord.Interaction, timezone: str):
    await timezone.timezone_cmd(interaction, bot, timezone)


@tree.command(name='unsettimezone', description='Undo custom timezone definition')
async def _unsettimezone(interaction: discord.Interaction):
    await unsettimezone.unsettimezone_cmd(interaction, bot)


@tree.command(name='mobile', description='Enable/disable MVP list mobile layout')
async def _mobile(interaction: discord.Interaction):
    await mobile.mobile(interaction, bot)


@tree.command(name='setminingchannel', description='Define a channel to track mining locations')
async def _setminingchannel(interaction: discord.Interaction):
    await set_mining_channel.setminingchannel(interaction, bot)


@tree.command(name='setmvpchannel', description='Define a channel to track MVPs')
async def _setmvpchannel(interaction: discord.Interaction):
    await set_mvp_channel.setmvpchannel(interaction, bot)


@tree.command(name='settings', description='Show bot settings')
async def _settings(interaction: discord.Interaction):
    await settings.settings_cmd(interaction, bot)


@tree.command(name='track', description='Track a MVP that has been defeated')
async def _track(interaction: discord.Interaction, mvp: str, time: str = None):
    await track.track(interaction, bot, mvp, time)


@tree.command(name='unsetminingchannel', description='Undo MVP track channel definition')
async def _unsetminingchannel(interaction: discord.Interaction):
    await unset_mining_channel.unsetminingchannel(interaction, bot)


@tree.command(name='unsetmvpchannel', description='Undo MVP track channel definition')
async def _unsetmvpchannel(interaction: discord.Interaction):
    await unset_mvp_channel.unsetmvpchannel(interaction, bot)


@tree.command(name='woe', description='Show War of Emperium times')
async def _woe(interaction: discord.Interaction):
    await woe.woe(interaction, bot)


@tree.command(name='gmc', description='Show GM Challenge times')
async def _gmc(interaction: discord.Interaction):
    await gmc.gmc(interaction, bot)


@tree.command(name='hh', description='Show BG Happy Hour times')
async def _hh(interaction: discord.Interaction):
    await hh.hh(interaction, bot)


@bot.event
async def on_ready():
    await on_ready.on_ready(bot, tree)


@bot.event
async def on_message(message: discord.Message):
    await on_message.on_message(bot, tree, message)


@bot.event
async def on_guild_join(guild):
    await on_guild_join.on_guild_join(guild, tree, bot)


@bot.event
async def on_guild_remove(guild):
    await on_guild_remove.on_guild_remove(guild, bot)


async def _run_bot(bot: Bot) -> None:
    log.info('Start bot client.')
    if bot.settings.bot_user_token is None:
        raise Exception('Bot token is missing')
    await bot.start(bot.settings.bot_user_token)


async def _run_timer(bot: Bot) -> None:
    log.info('Start timer.')
    from yellowtracker.timer import event_timer, track_timer
    while True:
        await event_timer.EventTimer.timer(bot)
        await track_timer.TrackTimer.timer(bot)
        await asyncio.sleep(bot.settings.timer_delay_secs)


async def main() -> None:
    await asyncio.gather(_run_bot(bot), _run_timer(bot))


if __name__ == '__main__':
    asyncio.run(main())
