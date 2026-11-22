from __future__ import annotations

import math
from datetime import datetime

from pytz import timezone


def fmt_time(milliseconds) -> str:
    minutes = math.floor(math.floor(math.fabs(milliseconds) / 1000) / 60)
    hours = math.floor(minutes / 60)
    days = math.floor(hours / 24)
    minutes = minutes % 60
    hours = hours % 24
    if minutes == 0 and hours == 0 and days == 0:
        return 'now'
    result = ''
    if days > 0:
        result += str(days) + (' day ' if days == 1 else ' days ')
    if hours > 0:
        result += str(hours) + (' hour ' if hours == 1 else ' hours ')
    if days == 0 and minutes > 0:
        result += str(minutes) + (' minute ' if minutes == 1 else ' minutes ')
    if milliseconds < 0:
        result += 'ago'
    elif milliseconds > 0:
        result = 'in ' + result
    return result.strip()


def fmt_time_short(milliseconds) -> str:
    minutes = math.floor(math.floor(math.fabs(milliseconds) / 1000) / 60)
    hours = math.floor(minutes / 60)
    days = math.floor(hours / 24)
    minutes = minutes % 60
    hours = hours % 24
    if minutes == 0 and hours == 0 and days == 0:
        return 'now'
    result = ''
    if days > 0:
        result += str(days) + 'd '
    if hours > 0:
        result += str(hours) + 'h '
    if days == 0 and minutes > 0:
        result += str(minutes) + 'm '
    if milliseconds < 0:
        result += 'ago'
    elif milliseconds > 0:
        result = 'in ' + result
    return result.strip()


def get_local_tzinfo():
    return datetime.now().astimezone().tzinfo


def fmt_dt(dt) -> str:
    return dt.strftime('%A %H:%M')


def get_dt_now(tz_str: str):
    dt_now = datetime.now()
    return dt_now.astimezone(timezone(tz_str))
