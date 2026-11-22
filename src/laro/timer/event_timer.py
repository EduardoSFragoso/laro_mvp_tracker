from __future__ import annotations

import logging
from datetime import timedelta

import discord

from laro.domain.bot import Bot
from laro.domain.emoji import Emoji
from laro.service import event_service
from laro.util.coroutine_util import run_coro
from laro.util.date_util import fmt_time_short, get_dt_now


log = logging.getLogger(__name__)

# Event types cycled for the bot presence.
# On the Ragnarok Online LATAM server only WoE runs on a fixed weekly schedule
# (GMC e Happy Hour estão removidos do projeto; ver docs/decisoes.md).
EVENT_TIMER_TYPES = ['woe']


class EventTimer:
    idx = 0

    @staticmethod
    async def timer(bot: Bot):
        if not bot.tracker_ready:
            return
        if bot.ws is None:
            return
        dt_now = get_dt_now(bot.settings.timezone)
        evt, ongoing = event_service.get_next_evt(bot, EVENT_TIMER_TYPES[EventTimer.idx % len(EVENT_TIMER_TYPES)])
        if evt is None:
            return
        msg = EventTimer.get_msg_prefix(evt)
        if ongoing:
            msg += ' ends '
            msg += fmt_time_short((evt['dt_end'] - dt_now) / timedelta(milliseconds=1))
        else:
            msg += ' '
            msg += fmt_time_short((evt['dt_begin'] - dt_now) / timedelta(milliseconds=1))
        game = discord.Game(name=msg)
        await run_coro(bot.change_presence(activity=game))
        EventTimer.idx = (EventTimer.idx + 1) % len(EVENT_TIMER_TYPES)

    @staticmethod
    def get_msg_prefix(evt: dict) -> str:
        msg = ''
        if evt['type'] == 'woe':
            msg += Emoji.WOE.value
        msg += evt['name']
        return msg
