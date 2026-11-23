from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import cast

import discord
import pytest

from laro.domain.bot import Bot
from laro.event import on_message as om


class _Channel:
    def __init__(self):
        self.sent = []

    async def send(self, msg):
        self.sent.append(msg)


def _make_message(content: str, channel: _Channel):
    # _dispatch_cmd só usa content/author/guild/channel/send dos stubs.
    return cast(
        discord.Message,
        SimpleNamespace(content=content, author=SimpleNamespace(), guild=SimpleNamespace(), channel=channel),
    )


def _make_bot():
    return cast(Bot, SimpleNamespace(settings=SimpleNamespace(command_prefix='!')))


@pytest.fixture()
def mobile_calls(monkeypatch):
    """Substitui mobile_core por um gravador e devolve a lista de chamadas."""
    calls = []

    async def _record(bot, message):
        calls.append(message)

    monkeypatch.setattr(om.mobile, 'mobile_core', _record)
    return calls


def test_mobile_chama_core(monkeypatch, mobile_calls):
    monkeypatch.setattr(om, '_is_guild_admin', lambda message: True)
    channel = _Channel()
    asyncio.run(om._dispatch_cmd(_make_bot(), _make_message('!mobile', channel)))
    assert len(mobile_calls) == 1
    assert channel.sent == []


def test_mobile_sem_admin(monkeypatch, mobile_calls):
    monkeypatch.setattr(om, '_is_guild_admin', lambda message: False)
    channel = _Channel()
    asyncio.run(om._dispatch_cmd(_make_bot(), _make_message('!mobile', channel)))
    assert mobile_calls == []
    assert len(channel.sent) == 1
    assert 'Gerenciar Servidor' in channel.sent[0]
