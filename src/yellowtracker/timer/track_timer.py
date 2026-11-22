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
                fresh_open = []
                if update_needed:
                    for entry_state in channel_state.entry_states:
                        track_util.calc_remaining_time(entry_state, entry_state.track_time)
                        if not entry_state.notified and 0 >= int(entry_state.r1) >= -1 and int(entry_state.r2) >= 0:
                            fresh_open.append(entry_state)
                    await channel_service.update_channel_message(bot, channel_state)
                # Janelas abertas (r1 <= 0 <= r2): mantêm/atualizam o aviso vivo
                # do canal; o ping da role acontece só quando algo abre agora.
                open_entries = [
                    entry_state
                    for entry_state in channel_state.entry_states
                    if int(entry_state.r1) <= 0 <= int(entry_state.r2)
                ]
                await channel_service.update_notification(
                    bot, channel_state, open_entries, new_windows=bool(fresh_open)
                )
                channel = channel_service.get_channel_from_guild(guild, channel_state.id_channel)
                if channel is None:
                    continue
                if channel_service.validate_channel(bot, channel) is not None:
                    continue
                await channel_service.delete_msgs(bot, channel_state, channel)
