from __future__ import annotations

import logging

from yellowtracker.domain.bot import Bot
from yellowtracker.service import channel_service
from yellowtracker.util import track_util


log = logging.getLogger(__name__)


class TrackTimer:
    @staticmethod
    async def timer(bot: Bot):
        if not bot.tracker_ready:
            return
        for guild in bot.guilds:
            guild_state = bot.get_guild_state(guild.id)
            if guild_state is None:
                continue
            for channel_state in list(guild_state.channel_states.values()):
                update_needed = len(channel_state.entry_states) > 0
                window_opened = []
                if update_needed:
                    for entry_state in channel_state.entry_states:
                        track_util.calc_remaining_time(entry_state, entry_state.track_time)
                        if not entry_state.notified and 0 >= int(entry_state.r1) >= -1 and int(entry_state.r2) >= 0:
                            window_opened.append(entry_state)
                    await channel_service.update_channel_message(bot, channel_state)
                if len(window_opened) > 0:
                    await channel_service.notify_entries(bot, channel_state, window_opened)
                channel = channel_service.get_channel_from_guild(guild, channel_state.id_channel)
                if channel is None:
                    continue
                if channel_service.validate_channel(bot, channel) is not None:
                    continue
                await channel_service.delete_msgs(bot, channel_state, channel)
