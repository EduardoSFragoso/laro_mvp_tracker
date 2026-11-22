from __future__ import annotations

import asyncio
import logging

import discord

from yellowtracker.command import (
    clean,
    # custom,  # /custom desligado no LATAM (ver docs/decisoes.md)
    set_mvp_channel,
    settings,
    track,
    unset_mvp_channel,
    unsettimezone,
    woe,
)
from yellowtracker.command.timezone import timezone_cmd
from yellowtracker.config import load_settings
from yellowtracker.domain.bot import Bot
from yellowtracker.domain.exceptions import BotConfigurationError
from yellowtracker.event.on_guild_join import on_guild_join as on_guild_join_evt
from yellowtracker.event.on_guild_remove import on_guild_remove as on_guild_remove_evt
from yellowtracker.event.on_message import on_message as on_message_evt
from yellowtracker.event.on_ready import on_ready as on_ready_evt


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


# /custom desligado no LATAM: MVPs não têm tempos custom cadastrados (o padrão
# do schema já cobre). Reativar: descomentar e importar yellowtracker.command.custom.
# @tree.command(name='custom', description='Enable/disable custom MVP respawn times')
# async def _custom(interaction: discord.Interaction):
#     await custom.custom_cmd(interaction, bot)


@tree.command(name='timezone', description='Define a custom timezone for MVP tracking')
async def _timezone(interaction: discord.Interaction, timezone: str):
    await timezone_cmd(interaction, bot, timezone)


@tree.command(name='unsettimezone', description='Undo custom timezone definition')
async def _unsettimezone(interaction: discord.Interaction):
    await unsettimezone.unsettimezone_cmd(interaction, bot)


# /mobile desligado no LATAM (feature antiga do server original).
# Reativar: descomentar e importar yellowtracker.command.mobile.
# @tree.command(name='mobile', description='Enable/disable MVP list mobile layout')
# async def _mobile(interaction: discord.Interaction):
#     await mobile.mobile(interaction, bot)


@tree.command(name='setmvpchannel', description='Define a channel to track MVPs')
async def _setmvpchannel(interaction: discord.Interaction):
    await set_mvp_channel.setmvpchannel(interaction, bot)


@tree.command(name='settings', description='Show bot settings')
async def _settings(interaction: discord.Interaction):
    await settings.settings_cmd(interaction, bot)


@tree.command(name='track', description='Track a MVP that has been defeated')
async def _track(interaction: discord.Interaction, mvp: str, time: str = None):
    await track.track(interaction, bot, mvp, time)


@tree.command(name='unsetmvpchannel', description='Undo MVP track channel definition')
async def _unsetmvpchannel(interaction: discord.Interaction):
    await unset_mvp_channel.unsetmvpchannel(interaction, bot)


@tree.command(name='woe', description='Show War of Emperium times')
async def _woe(interaction: discord.Interaction):
    await woe.woe(interaction, bot)


@bot.event
async def on_ready():
    await on_ready_evt(bot, tree)


@bot.event
async def on_message(message: discord.Message):
    await on_message_evt(bot, tree, message)


@bot.event
async def on_guild_join(guild):
    await on_guild_join_evt(guild, tree, bot)


@bot.event
async def on_guild_remove(guild):
    await on_guild_remove_evt(guild, bot)


async def _run_bot(bot: Bot) -> None:
    log.info('Start bot client.')
    if bot.settings.bot_user_token is None:
        raise BotConfigurationError('Bot token is missing')
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
