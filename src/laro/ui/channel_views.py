from __future__ import annotations

import discord

from laro.domain.bot import Bot
from laro.domain.models import ChannelState, Mvp
from laro.domain.track_type import TrackType
from laro.util.coroutine_util import run_coro
from laro.util.interaction_util import is_confirmation_owner_admin


class SetChannelView(discord.ui.View):
    def __init__(self, *, timeout=180, bot: Bot, trackType: TrackType, requester_id: int):
        super().__init__(timeout=timeout)
        self.requester_id = requester_id
        self.add_item(SetChannelYesButton(bot=bot, trackType=trackType))
        self.add_item(SetChannelNoButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await is_confirmation_owner_admin(interaction, self.requester_id)


class SetChannelYesButton(discord.ui.Button):
    def __init__(self, bot: Bot, trackType: TrackType):
        self.bot = bot
        self.trackType = trackType
        super().__init__(style=discord.ButtonStyle.primary, label='Yes')

    async def callback(self, interaction: discord.Interaction):
        await run_coro(interaction.response.edit_message(view=None))
        channel = interaction.channel
        if isinstance(channel, discord.TextChannel):
            from laro.service import channel_service

            await channel_service.set_channel(self.bot, channel, self.trackType)


class SetChannelNoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label='No')

    async def callback(self, interaction: discord.Interaction):
        await run_coro(interaction.response.edit_message(view=None))


class TrackView(discord.ui.View):
    def __init__(self, *, timeout=180, bot: Bot, opts: list[Mvp], mins_ago: int, user_time: str | None):
        super().__init__(timeout=timeout)
        self.add_item(TrackSelect(bot=bot, opts=opts, mins_ago=mins_ago, user_time=user_time))


class TrackSelect(discord.ui.Select):
    def __init__(self, bot: Bot, opts: list[Mvp], mins_ago: int, user_time: str | None):
        self.bot = bot
        self.opts = opts
        self.mins_ago = mins_ago
        self.user_time = user_time
        options = [
            discord.SelectOption(label=opt.name, description=opt.display_map, value=str(opt.id)) for opt in self.opts
        ]
        super().__init__(placeholder='Select an option', options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild_id is None or interaction.channel_id is None:
            return
        entry = next((x for x in self.opts if str(x.id) == self.values[0]), None)
        guild_state = self.bot.get_guild_state(interaction.guild_id)
        if guild_state is None or entry is None:
            return
        channel_state = guild_state.channel_states.get(interaction.channel_id)
        if channel_state is None:
            return
        from laro.service import channel_service

        bot_reply_msg = await channel_service.update_track_time(
            self.bot, guild_state, channel_state, entry, self.mins_ago, self.user_time, interaction.user.id
        )
        await run_coro(interaction.response.edit_message(content=bot_reply_msg, view=None))


class ChannelMessageView(discord.ui.View):
    def __init__(self, *, timeout=None, bot: Bot, channel_state: ChannelState):
        super().__init__(timeout=timeout)
        self.add_item(ChannelMessageTrackButton(bot=bot, channel_state=channel_state))


class ChannelMessageTrackButton(discord.ui.Button):
    def __init__(self, bot: Bot, channel_state: ChannelState):
        self.bot = bot
        self.channel_state = channel_state
        super().__init__(style=discord.ButtonStyle.primary, emoji='➕', label=f'TRACK {channel_state.type.desc}')

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ChannelMessageTrackModal(bot=self.bot, channel_state=self.channel_state))


class ChannelMessageTrackModal(discord.ui.Modal):
    def __init__(self, bot: Bot, channel_state: ChannelState):
        super().__init__(title=f'TRACK {channel_state.type.desc}')
        self.bot = bot
        self.channel_state = channel_state
        self.name_input = discord.ui.TextInput(label='Name')
        self.time_input = discord.ui.TextInput(label='Time', required=False)
        self.add_item(self.name_input)
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.strip()
        if len(name) > 0:
            user_time = self.time_input.value.strip()
            if len(user_time) == 0:
                user_time = None
            from laro.service import channel_service

            await channel_service.track_by_interaction(self.bot, interaction, self.channel_state, name, user_time)
