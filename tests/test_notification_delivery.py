from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import discord

from laro.config import Settings
from laro.domain.bot import Bot
from laro.domain.models import ChannelState, GuildState, Mvp, TrackEntryState
from laro.domain.track_type import TrackType
from laro.service.channel_service import update_notification


def test_failed_notification_send_does_not_mark_entry_notified():
    entry = Mvp(id=1, name='Amon Ra', map='moc_pryd06', t1=60, t2=70)
    entry_state = TrackEntryState(
        entry=entry,
        track_time=datetime.now(),
        t1=60,
        t2=70,
        r1=0,
        r2=10,
    )
    channel_state = ChannelState(id_channel=2, id_guild=1, type=TrackType.MVP)
    guild_state = GuildState(id_guild=1)
    connection = SimpleNamespace(execute=AsyncMock())
    sent_message = object()
    channel = SimpleNamespace(
        id=2,
        send=AsyncMock(side_effect=[discord.DiscordException('temporary failure'), sent_message]),
    )
    guild = SimpleNamespace(id=1, text_channels=[channel], get_role=lambda _role_id: None)
    bot = cast(
        Bot,
        SimpleNamespace(
            guilds=[guild],
            settings=Settings(bot_user_token=None, database_url=None),
            get_guild_state=lambda _guild_id: guild_state,
            pool_acquire=AsyncMock(return_value=connection),
            pool_release=AsyncMock(),
        ),
    )

    async def scenario():
        entry_state.notification_pending = True
        await update_notification(bot, channel_state, [entry_state], new_entries=[entry_state])
        assert entry_state.notified is False
        assert entry_state.notification_pending is True
        connection.execute.assert_not_awaited()

        entry_state.r1 = -2
        await update_notification(bot, channel_state, [entry_state], new_entries=[entry_state])
        assert entry_state.notified is True
        assert entry_state.notification_pending is False
        assert channel_state.notification_message is sent_message
        connection.execute.assert_awaited_once()

    asyncio.run(scenario())
