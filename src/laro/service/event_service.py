from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timedelta

import discord
from pytz import timezone

from laro.domain.bot import Bot
from laro.domain.weekly_event import Evt, WeeklyEvent, WeeklyEvtTemplate
from laro.util.date_util import fmt_dt, get_dt_now, get_local_tzinfo


EMPTY_SLOT = '—'


def get_woe_map(bot: Bot) -> dict[str, str]:
    """Map the WoE events onto the fixed Saturday/Sunday embed fields."""
    return _evt_map(
        bot,
        'woe',
        keys=('saturday', 'sunday'),
        key_of=lambda weekday, _today, _tomorrow: 'saturday' if weekday != 7 else 'sunday',
    )


def _evt_map(
    bot: Bot, type: str, keys: tuple[str, ...], key_of: Callable[[int, int, int], str | None]
) -> dict[str, str]:
    """Build the {ongoing/next/<days>} string map for one event type.

    The event type with no scheduled events still yields a complete map with
    '#' placeholders so the commands never break or show empty fields.
    """
    dt_now = get_dt_now(bot.settings.timezone)
    weekday_today = dt_now.isoweekday()
    weekday_tomorrow = 1 if weekday_today == 7 else weekday_today + 1
    result: dict[str, str] = {'ongoing': '', 'next': EMPTY_SLOT, **dict.fromkeys(keys, EMPTY_SLOT)}
    next_evt: Evt | None = None
    for evt in get_evts(bot, type):
        key = key_of(int(evt['weekday']), weekday_today, weekday_tomorrow)
        if key in result:
            result[key] = format_evt(bot, evt) + '\n'
        if evt['dt_begin'] <= dt_now <= evt['dt_end']:
            result['ongoing'] = format_evt(bot, evt)
        if evt['dt_begin'] > dt_now and (next_evt is None or evt['dt_begin'] < next_evt['dt_begin']):
            next_evt = evt
    if next_evt is not None:
        result['next'] = format_evt(bot, next_evt)
    return result


def build_evt_embed(bot: Bot, emoji: str, title: str, evt_map: dict[str, str]) -> discord.Embed:
    """Format an event map as a Discord embed with the day fields in map order."""
    embed = discord.Embed()
    embed.title = f'{emoji} {title}'
    embed.colour = discord.Colour.gold()
    if evt_map['ongoing'] != '':
        embed.add_field(name='Ongoing :boom:', value=evt_map['ongoing'], inline=False)
    embed.add_field(name='Next :arrow_right:', value=evt_map['next'], inline=False)
    day_keys = [key for key in evt_map if key not in ('ongoing', 'next')]
    for key in day_keys:
        embed.add_field(name=key.capitalize(), value=evt_map[key].rstrip('\n'), inline=False)
    footer = 'Server Time (' + bot.settings.timezone + '): '
    footer += fmt_dt(get_dt_now(bot.settings.timezone))
    embed.set_footer(text=footer)
    return embed


def get_next_evt(bot: Bot, type: str | None = None, dt_now: datetime | None = None) -> tuple[Evt | None, bool]:
    """Next occurrence of the event type, plus whether it is ongoing now.

    Tests inject dt_now to pin the clock; production omits it and uses now.
    """
    tzinfo = timezone(bot.settings.timezone)
    if dt_now is None:
        dt_now = get_dt_now(bot.settings.timezone)
    elif dt_now.tzinfo is None:
        dt_now = tzinfo.localize(dt_now, is_dst=False)
    evts = get_evts(bot, type, dt_now=dt_now)
    next_evt = None
    ongoing = False
    for evt in evts:
        if evt['dt_end'] < dt_now:
            continue
        if next_evt is None:
            next_evt = evt
        if evt['dt_begin'] <= dt_now <= evt['dt_end']:  # ongoing
            ongoing = True
            break
        if evt['dt_begin'] < next_evt['dt_begin']:  # next
            next_evt = evt
    return next_evt, ongoing


def is_ongoing(bot: Bot, evt: Evt) -> bool:
    dt_now = get_dt_now(bot.settings.timezone)
    return evt['dt_begin'] <= dt_now <= evt['dt_end']


def format_evt(bot: Bot, evt: Evt) -> str:
    local_tz = get_local_tzinfo()
    dt_now = get_dt_now(bot.settings.timezone)
    result = '**'
    result += evt['name']
    result += '** '
    result += f'<t:{int(time.mktime(evt["dt_begin"].astimezone(tz=local_tz).timetuple()))}:f>'
    if evt['dt_begin'] <= dt_now <= evt['dt_end']:
        result += ' (ends '
        result += f'<t:{int(time.mktime(evt["dt_end"].astimezone(tz=local_tz).timetuple()))}:R>'
    else:
        result += ' ('
        result += f'<t:{int(time.mktime(evt["dt_begin"].astimezone(tz=local_tz).timetuple()))}:R>'
    result += ')'
    return result


def get_evts(bot: Bot, type: str | None = None, dt_now: datetime | None = None) -> list[Evt]:
    """Occurrences of the weekly events around dt_now (defaults to now).

    An occurrence that already ended rolls forward one week, so the search
    never comes back empty on the day the event just finished (e.g. the WoE
    on Sunday night between 22:00 and 24:00).
    """
    if dt_now is None:
        dt_now = get_dt_now(bot.settings.timezone)
    elif dt_now.tzinfo is None:
        dt_now = timezone(bot.settings.timezone).localize(dt_now, is_dst=False)
    tzinfo = timezone(bot.settings.timezone)
    result: list[Evt] = []
    for evt in WeeklyEvent.DATA:
        if type is not None and evt['type'] != type:
            continue
        dt_evt_begin = _weekly_evt_dt(bot, tzinfo, evt, 'begin', dt_now)
        dt_evt_end = _weekly_evt_dt(bot, tzinfo, evt, 'end', dt_now)
        if dt_evt_end < dt_evt_begin:
            dt_evt_end += timedelta(days=1)
        if dt_evt_end <= dt_now:
            dt_evt_begin += timedelta(days=7)
            dt_evt_end += timedelta(days=7)
        evtcp: Evt = {**evt, 'dt_begin': dt_evt_begin, 'dt_end': dt_evt_end}
        result.append(evtcp)
    result.sort(key=lambda x: x['dt_begin'])
    return result


def _weekly_evt_dt(bot: Bot, tzinfo, evt: WeeklyEvtTemplate, begin_or_end: str, dt_now: datetime):
    parts = evt[begin_or_end].split(':')
    dt = dt_now.replace(
        hour=int(parts[0]),
        minute=int(parts[1]),
        second=0,
        microsecond=0,
    )
    while dt.isoweekday() != int(evt['weekday']):
        dt += timedelta(days=1)
    dt = tzinfo.localize(dt.replace(tzinfo=None), is_dst=False)
    return dt
