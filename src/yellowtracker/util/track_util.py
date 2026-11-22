from __future__ import annotations

from datetime import datetime

from yellowtracker.domain.models import ChannelState, TrackEntryState
from yellowtracker.domain.track_type import TrackType


def track_entry(channel_state: ChannelState, entry, track_time: datetime,
                custom: bool = False) -> TrackEntryState:
    """Register (or update) a tracked entry in a channel and return its state."""
    entry_state = next(
        (x for x in channel_state.entry_states if x.entry is entry),
        None,
    )
    if entry_state is None:
        entry_state = TrackEntryState(entry=entry, track_time=track_time, t1=-999)
        if channel_state.type == TrackType.MVP:
            entry_state.t2 = -999
        channel_state.entry_states.append(entry_state)

    entry_state.t1 = entry.t1
    if channel_state.type == TrackType.MVP:
        entry_state.t2 = entry.t2
        if custom and entry.t1custom is not None:
            entry_state.t1 = entry.t1custom
            entry_state.t2 = entry.t2custom

    entry_state.track_time = track_time
    calc_remaining_time(entry_state, track_time, channel_state.type)
    if channel_state.type == TrackType.MINING:
        channel_state.entry_states.sort(key=lambda e: e.r1)
    else:
        channel_state.entry_states.sort(key=lambda e: e.r2)
    return entry_state


def calc_remaining_time(entry_state: TrackEntryState, track_time: datetime,
                        type: TrackType) -> None:
    mins_ago = round((datetime.now() - track_time).total_seconds() / 60)
    entry_state.r1 = entry_state.t1 - mins_ago
    if type == TrackType.MVP:
        entry_state.r2 = entry_state.t2 - mins_ago


def fmt_r1_r2(val: int) -> str:
    return str(val) if val > 0 else '**' + str(val) + '**'


def fmt_column(values: list[str]) -> str:
    return '\n'.join(values)
