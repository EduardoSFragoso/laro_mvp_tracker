from __future__ import annotations

import logging


log = logging.getLogger(__name__)


async def run_coro(coroutine):
    """Run a coroutine, logging (instead of raising) any unexpected error.

    Discord callbacks should never crash the whole bot because a single
    message/response failed, so this is the default wrapper used everywhere.
    """
    try:
        return await coroutine
    except BaseException:
        log.error('Unexpected error.', exc_info=True)
