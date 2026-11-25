from __future__ import annotations

import discord

from laro.config import Settings
from laro.domain.bot import Bot


def test_bot_disables_mentions_by_default_but_allows_explicit_roles():
    bot = Bot(Settings(bot_user_token=None, database_url=None), intents=discord.Intents.none())

    assert bot.allowed_mentions is not None
    assert bot.allowed_mentions.to_dict() == {'parse': []}

    role = discord.Object(id=123)
    role_mentions = bot.allowed_mentions.merge(discord.AllowedMentions(roles=[role]))
    assert role_mentions.to_dict() == {'roles': [123], 'parse': []}
