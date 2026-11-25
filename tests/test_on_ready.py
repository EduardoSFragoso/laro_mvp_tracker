from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

from laro.domain.bot import Bot
from laro.event import on_ready as on_ready_module


def test_on_ready_reuses_pool_after_gateway_reconnect(monkeypatch):
    pool = object()
    connection = object()
    pool_acquire = AsyncMock(return_value=connection)
    pool_release = AsyncMock()
    bot = cast(
        Bot,
        SimpleNamespace(
            user=None,
            guilds=[],
            settings=SimpleNamespace(database_url='postgres://test', command_prefix='!'),
            pool=pool,
            tracker_ready=True,
            pool_acquire=pool_acquire,
            pool_release=pool_release,
            change_presence=AsyncMock(),
        ),
    )
    load_database = AsyncMock()
    create_pool = AsyncMock()
    monkeypatch.setattr(on_ready_module, 'load_database', load_database)
    monkeypatch.setattr(on_ready_module.asyncpg, 'create_pool', create_pool)

    asyncio.run(on_ready_module.on_ready(bot))

    create_pool.assert_not_awaited()
    load_database.assert_awaited_once_with(bot, connection)
    pool_release.assert_awaited_once_with(connection)
    assert bot.pool is pool
    assert bot.tracker_ready is True
