from __future__ import annotations

import asyncio
import logging

import discord

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


@bot.event
async def on_ready():
    await on_ready_evt(bot)


@bot.event
async def on_message(message: discord.Message):
    await on_message_evt(bot, message)


@bot.event
async def on_guild_join(guild):
    await on_guild_join_evt(guild, bot)


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
