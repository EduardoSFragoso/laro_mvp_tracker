from __future__ import annotations

import asyncio

import pytest

from laro.util.coroutine_util import run_coro


def test_run_coro_propagates_cancellation():
    async def cancelled():
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(run_coro(cancelled()))
