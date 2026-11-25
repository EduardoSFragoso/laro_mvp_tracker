from __future__ import annotations

import logging
from collections.abc import Coroutine
from typing import Any

import discord


log = logging.getLogger(__name__)


async def run_coro[T](coroutine: Coroutine[Any, Any, T]) -> T | None:
    """Run a Discord API coroutine, logging expected API failures.

    Programming errors should remain visible to the caller instead of being
    mistaken for a recoverable Discord failure.
    """
    try:
        return await coroutine
    except discord.DiscordException:
        log.warning('Discord request failed.', exc_info=True)
