from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import discord
import pytest

from laro.command.clean import CleanView
from laro.domain.bot import Bot
from laro.domain.track_type import TrackType
from laro.service.channel_service import SetChannelView


@pytest.mark.parametrize('view_type', [CleanView, SetChannelView])
def test_confirmation_view_allows_only_requesting_admin(view_type):
    requester_id = 42
    bot = cast(Bot, SimpleNamespace())
    view = view_type(bot=bot, trackType=TrackType.MVP, requester_id=requester_id)

    owner = SimpleNamespace(id=requester_id, guild_permissions=SimpleNamespace(manage_guild=True))
    owner_response = AsyncMock()
    owner_interaction = cast(
        discord.Interaction,
        SimpleNamespace(user=owner, response=SimpleNamespace(send_message=owner_response)),
    )
    assert asyncio.run(view.interaction_check(owner_interaction)) is True
    owner_response.assert_not_awaited()

    another_admin = SimpleNamespace(id=99, guild_permissions=SimpleNamespace(manage_guild=True))
    other_response = AsyncMock()
    other_interaction = cast(
        discord.Interaction,
        SimpleNamespace(user=another_admin, response=SimpleNamespace(send_message=other_response)),
    )
    assert asyncio.run(view.interaction_check(other_interaction)) is False
    other_response.assert_awaited_once_with(
        'Apenas quem iniciou a ação e ainda tem a permissão Gerenciar Servidor pode usar estes botões.',
        ephemeral=True,
    )

    owner_without_permission = SimpleNamespace(id=requester_id, guild_permissions=SimpleNamespace(manage_guild=False))
    revoked_response = AsyncMock()
    revoked_interaction = cast(
        discord.Interaction,
        SimpleNamespace(user=owner_without_permission, response=SimpleNamespace(send_message=revoked_response)),
    )
    assert asyncio.run(view.interaction_check(revoked_interaction)) is False
    revoked_response.assert_awaited_once()
