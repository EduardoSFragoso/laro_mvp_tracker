from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.domain.track_type import TrackType
from laro.service import channel_service
from laro.util.coroutine_util import run_coro
from laro.util.interaction_util import is_confirmation_owner_admin


async def clean_core(bot: Bot, message: discord.Message) -> None:
    validate_msg = channel_service.validate_channel(bot, message.channel)
    if validate_msg is not None:
        await run_coro(message.channel.send(validate_msg))
        return
    if message.guild is None:
        return
    guild_state = bot.get_guild_state(message.guild.id)
    if guild_state is None:
        return
    channel_state = guild_state.channel_states.get(message.channel.id)
    if channel_state is None:
        await run_coro(message.channel.send('This command can only be used in a track channel.'))
        return

    await run_coro(
        message.channel.send(
            'This will clean the list. Are you sure?',
            view=CleanView(bot=bot, trackType=channel_state.type, requester_id=message.author.id),
        )
    )


class CleanView(discord.ui.View):
    def __init__(self, *, timeout=180, bot: Bot, trackType: TrackType, requester_id: int):
        super().__init__(timeout=timeout)
        self.requester_id = requester_id
        self.add_item(CleanYesButton(bot=bot, trackType=trackType))
        self.add_item(CleanNoButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await is_confirmation_owner_admin(interaction, self.requester_id)


class CleanYesButton(discord.ui.Button):
    def __init__(self, bot: Bot, trackType: TrackType):
        self.bot = bot
        self.trackType = trackType
        super().__init__(style=discord.ButtonStyle.primary, label='Yes')

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild_id is None or interaction.channel_id is None:
            await run_coro(interaction.response.defer())
            return
        bot = self.bot
        guild_state = bot.get_guild_state(interaction.guild_id)
        if guild_state is None:
            await run_coro(interaction.response.defer())
            return
        channel_state = guild_state.channel_states.get(interaction.channel_id)
        if channel_state is None:
            await run_coro(interaction.response.defer())
            return
        key = 't2' if self.trackType == TrackType.MVP else 't1'
        for entry_state in channel_state.entry_states:
            mins_ago = getattr(entry_state, key)
            mins_ago += bot.settings.table_entry_expiration_mins
            entry_state.r1 = -mins_ago
            if self.trackType == TrackType.MVP:
                entry_state.r2 = -mins_ago
        await channel_service.update_channel_message(bot, channel_state)
        await run_coro(interaction.response.edit_message(content='Track list cleared.', view=None))


class CleanNoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label='No')

    async def callback(self, interaction: discord.Interaction):
        await run_coro(interaction.response.edit_message(view=None))
