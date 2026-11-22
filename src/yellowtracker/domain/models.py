from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from yellowtracker.domain.track_type import TrackType


@dataclass
class Mvp:
    """An MVP entry as loaded from the database."""

    id: int
    name: str
    map: str
    t1: int  # minimum respawn time in minutes
    t2: int  # maximum respawn time in minutes
    t1custom: int | None = None
    t2custom: int | None = None
    id_mob: int | None = None
    navi: str | None = None  # kRO map code shown to the user (e.g. gon_dun03)
    alias: list[str] = field(default_factory=list)

    @property
    def display_map(self) -> str:
        """The map as shown to the user: the navi code when known, else the map name."""
        return self.navi if self.navi is not None else self.map


@dataclass
class EntryLog:
    """A log entry for the last tracked MVPs of a channel."""

    entry: Mvp
    date: datetime
    id_user: int


@dataclass
class TrackEntryState:
    """Runtime state of a tracked MVP within a channel."""

    entry: Mvp
    track_time: datetime
    t1: int  # effective window, in minutes
    t2: int = -999
    r1: int = -999
    r2: int = -999


@dataclass
class ChannelState:
    """Runtime state of a track channel."""

    id_channel: int
    id_guild: int
    type: TrackType
    id_message: int | None = None
    id_help_message: int | None = None
    entry_states: list[TrackEntryState] = field(default_factory=list)
    entry_logs: deque[EntryLog] = field(default_factory=deque)


@dataclass
class GuildState:
    """Runtime state of a guild (discord server)."""

    id_guild: int
    custom: bool = True
    mobile: bool = False
    timezone: str | None = None
    id_mvp_channel: int | None = None
    channel_states: dict[int, ChannelState] = field(default_factory=dict)

    def get_channel_state(self, type: TrackType) -> ChannelState | None:
        return next(
            (cs for cs in self.channel_states.values() if cs.type == type),
            None,
        )

    def remove_channel_state(self, type: TrackType) -> ChannelState | None:
        channel_state = self.get_channel_state(type)
        if channel_state is not None:
            del self.channel_states[channel_state.id_channel]
        return channel_state
