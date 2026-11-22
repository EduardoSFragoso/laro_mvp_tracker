from __future__ import annotations

import time

from pytz import timezone
from datetime import timedelta

from yellowtracker.domain.bot import Bot
from yellowtracker.domain.weekly_event import WeeklyEvent
from yellowtracker.util.date_util import get_dt_now, get_local_tzinfo

EMPTY_SLOT = '—'


def get_gmc_map(bot: Bot) -> dict[str, str]:
    dt_now = get_dt_now(bot.settings.timezone)
    weekday_today = dt_now.isoweekday()
    weekday_tomorrow = 1 if weekday_today == 7 else (weekday_today + 1)
    evts = get_evts(bot, type='gmc')
    gmc_map = {'ongoing': '', 'next': EMPTY_SLOT, 'today': EMPTY_SLOT, 'tomorrow': EMPTY_SLOT}
    if not evts:
        return gmc_map
    next_evt = evts[0]
    for evt in evts:
        str_gmc = format_evt(bot, evt) + '\n'
        if int(evt['weekday']) == weekday_today:
            gmc_map['today'] = str_gmc
        elif int(evt['weekday']) == weekday_tomorrow:
            gmc_map['tomorrow'] = str_gmc
        if evt['dt_begin'] <= dt_now <= evt['dt_end']:
            gmc_map['ongoing'] = format_evt(bot, evt)
        if evt['dt_begin'] <= dt_now:
            continue
        if next_evt['dt_begin'] <= dt_now or evt['dt_begin'] < next_evt['dt_begin']:
            next_evt = evt
    gmc_map['next'] = format_evt(bot, next_evt)
    return gmc_map


def get_hh_map(bot: Bot) -> dict[str, str]:
    dt_now = get_dt_now(bot.settings.timezone)
    weekday_today = dt_now.isoweekday()
    weekday_tomorrow = 1 if weekday_today == 7 else (weekday_today + 1)
    evts = get_evts(bot, type='hh')
    hh_map = {'ongoing': '', 'next': EMPTY_SLOT, 'today': EMPTY_SLOT, 'tomorrow': EMPTY_SLOT}
    if not evts:
        return hh_map
    next_evt = evts[0]
    for evt in evts:
        str_hh = format_evt(bot, evt) + '\n'
        if int(evt['weekday']) == weekday_today:
            hh_map['today'] = str_hh
        elif int(evt['weekday']) == weekday_tomorrow:
            hh_map['tomorrow'] = str_hh
        if evt['dt_begin'] <= dt_now <= evt['dt_end']:
            hh_map['ongoing'] = format_evt(bot, evt)
        if evt['dt_begin'] <= dt_now:
            continue
        if next_evt['dt_begin'] <= dt_now or evt['dt_begin'] < next_evt['dt_begin']:
            next_evt = evt
    hh_map['next'] = format_evt(bot, next_evt)
    return hh_map


def get_woe_map(bot: Bot) -> dict[str, str]:
    dt_now = get_dt_now(bot.settings.timezone)
    evts = get_evts(bot, type='woe')
    woe_map = {'ongoing': '', 'next': EMPTY_SLOT, 'saturday': EMPTY_SLOT, 'sunday': EMPTY_SLOT}
    if not evts:
        return woe_map
    next_evt = evts[0]
    for evt in evts:
        str_woe = format_evt(bot, evt) + '\n'
        if int(evt['weekday']) == 7:
            woe_map['sunday'] = str_woe
        else:
            woe_map['saturday'] = str_woe
        if evt['dt_begin'] <= dt_now <= evt['dt_end']:
            woe_map['ongoing'] = format_evt(bot, evt)
        if evt['dt_begin'] <= dt_now:
            continue
        if next_evt['dt_begin'] <= dt_now or evt['dt_begin'] < next_evt['dt_begin']:
            next_evt = evt
    woe_map['next'] = format_evt(bot, next_evt)
    return woe_map


def get_next_evt(bot: Bot, type: str = None) -> tuple[dict | None, bool]:
    dt_now = get_dt_now(bot.settings.timezone)
    evts = get_evts(bot, type)
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


def is_ongoing(bot: Bot, evt: dict) -> bool:
    dt_now = get_dt_now(bot.settings.timezone)
    return evt['dt_begin'] <= dt_now <= evt['dt_end']


def format_evt(bot: Bot, evt: dict) -> str:
    local_tz = get_local_tzinfo()
    dt_now = get_dt_now(bot.settings.timezone)
    result = '**'
    result += evt['name']
    result += '** '
    result += f"<t:{int(time.mktime(evt['dt_begin'].astimezone(tz=local_tz).timetuple()))}:f>"
    if evt['dt_begin'] <= dt_now <= evt['dt_end']:
        result += ' (ends '
        result += f"<t:{int(time.mktime(evt['dt_end'].astimezone(tz=local_tz).timetuple()))}:R>"
    else:
        result += ' ('
        result += f"<t:{int(time.mktime(evt['dt_begin'].astimezone(tz=local_tz).timetuple()))}:R>"
    result += ')'
    return result


def get_evts(bot: Bot, type: str = None) -> list[dict]:
    tzinfo = timezone(bot.settings.timezone)
    result = []
    for evt in WeeklyEvent.DATA:
        if type is not None and evt['type'] != type:
            continue
        dt_evt_begin = _weekly_evt_dt(bot, tzinfo, evt, 'begin')
        dt_evt_end = _weekly_evt_dt(bot, tzinfo, evt, 'end')
        if dt_evt_end < dt_evt_begin:
            dt_evt_end += timedelta(days=1)
        evtcp = dict(evt)
        evtcp['dt_begin'] = dt_evt_begin
        evtcp['dt_end'] = dt_evt_end
        result.append(evtcp)
    result.sort(key=lambda x: x['dt_begin'])
    return result


def _weekly_evt_dt(bot: Bot, tzinfo, evt: dict, begin_or_end: str):
    parts = evt[begin_or_end].split(':')
    dt = get_dt_now(bot.settings.timezone).replace(
        hour=int(parts[0]),
        minute=int(parts[1]),
        second=0,
        microsecond=0,
    )
    while dt.isoweekday() != int(evt['weekday']):
        dt += timedelta(days=1)
    dt = tzinfo.localize(dt.replace(tzinfo=None), is_dst=False)
    return dt
