from datetime import datetime, timedelta

from yellowtracker.domain.models import ChannelState, Mvp, TrackEntryState
from yellowtracker.domain.track_type import TrackType
from yellowtracker.util import track_util


def make_mvp_channel(mobile=False):
    return ChannelState(id_channel=1, id_guild=100, type=TrackType.MVP)


def make_mvp(**overrides):
    data = {
        'id': 1,
        'name': 'Amon Ra',
        'map': 'Subsolo da Pirâmide (2)',
        't1': 60,
        't2': 70,
    }
    data.update(overrides)
    return Mvp(**data)


def test_track_entry_sets_window():
    channel_state = make_mvp_channel()
    mvp = make_mvp()
    now = datetime.now()
    entry_state = track_util.track_entry(channel_state, mvp, now)
    assert entry_state.t1 == 60
    assert entry_state.t2 == 70
    assert entry_state.r1 == 60
    assert entry_state.r2 == 70
    assert channel_state.entry_states == [entry_state]


def test_track_entry_custom_window():
    channel_state = make_mvp_channel()
    mvp = make_mvp(t1custom=55, t2custom=75)
    now = datetime.now()
    entry_state = track_util.track_entry(channel_state, mvp, now, custom=True)
    assert entry_state.t1 == 55
    assert entry_state.t2 == 75
    assert entry_state.r1 in (54, 55)


def test_track_entry_custom_ignored_without_flag():
    channel_state = make_mvp_channel()
    mvp = make_mvp(t1custom=55, t2custom=75)
    now = datetime.now()
    entry_state = track_util.track_entry(channel_state, mvp, now, custom=False)
    assert entry_state.t1 == 60
    assert entry_state.t2 == 70


def test_track_entry_custom_ignored_when_null():
    channel_state = make_mvp_channel()
    mvp = make_mvp()
    now = datetime.now()
    entry_state = track_util.track_entry(channel_state, mvp, now, custom=True)
    assert entry_state.t1 == 60
    assert entry_state.t2 == 70
    assert entry_state.r1 in (59, 60)


def test_track_entry_reuse_existing_state():
    channel_state = make_mvp_channel()
    mvp = make_mvp()
    now = datetime.now()
    first = track_util.track_entry(channel_state, mvp, now)
    later = now + timedelta(minutes=30)
    second = track_util.track_entry(channel_state, mvp, later)
    assert first is second
    assert len(channel_state.entry_states) == 1


def test_sort_by_r2_for_mvp():
    channel_state = make_mvp_channel()
    now = datetime.now()
    track_util.track_entry(channel_state, make_mvp(id=1, name='A', t1=60, t2=70), now)
    track_util.track_entry(channel_state, make_mvp(id=2, name='B', t1=120, t2=130), now)
    assert [e.entry.name for e in channel_state.entry_states] == ['A', 'B']
    track_util.track_entry(channel_state, make_mvp(id=3, name='C', t1=10, t2=20), now)
    assert [e.entry.name for e in channel_state.entry_states] == ['C', 'A', 'B']


def test_calc_remaining_time_updates_both():
    entry_state = TrackEntryState(entry=None, track_time=datetime.now(), t1=60, t2=70)
    track_time = datetime.now() - timedelta(minutes=5)
    entry_state.track_time = track_time
    track_util.calc_remaining_time(entry_state, track_time)
    assert entry_state.r1 == 55
    assert entry_state.r2 == 65


def test_fmt_r1_r2_bold_negative():
    assert track_util.fmt_r1_r2(10) == '10'
    assert track_util.fmt_r1_r2(-5) == '**-5**'
    assert track_util.fmt_r1_r2(0) == '**0**'


def test_fmt_column_joins_with_newlines():
    assert track_util.fmt_column(['a', 'b']) == 'a\nb'
    assert track_util.fmt_column(['a']) == 'a'
    assert track_util.fmt_column([]) == ''
