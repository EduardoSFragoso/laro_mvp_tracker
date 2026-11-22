from laro.config import Settings
from laro.domain.models import ChannelState
from laro.domain.track_type import TrackType
from laro.service.channel_service import _multiple_matches_msg, _resolve_query, parse_user_time


def test_parse_user_time_rejects_bad_format():
    assert parse_user_time('America/Sao_Paulo', '123') == 'HHMM format expected for user time'
    assert parse_user_time('America/Sao_Paulo', '12345') == 'HHMM format expected for user time'
    assert parse_user_time('America/Sao_Paulo', 'abcd') == 'HHMM format expected for user time'


def test_parse_user_time_rejects_out_of_range():
    assert parse_user_time('America/Sao_Paulo', '2400') == 'HH must be between 00 and 23'
    assert parse_user_time('America/Sao_Paulo', '1060') == 'MM must be between 00 and 59'


def test_parse_user_time_returns_datetime():
    from datetime import datetime, timedelta

    result = parse_user_time('America/Sao_Paulo', '2359')
    assert isinstance(result, datetime)
    # track time must always be in the past (max 24h)
    assert result.tzinfo is not None
    assert (datetime.now(result.tzinfo) - result) < timedelta(days=1)


def test_multiple_matches_msg_mentions_time():
    msg = _multiple_matches_msg(TrackType.MVP, 'atroce', '1234')
    assert 'atroce' in msg
    assert '1234' in msg


def test_multiple_matches_msg_no_time():
    msg = _multiple_matches_msg(TrackType.MVP, 'atroce', None)
    assert 'atroce' in msg
    assert 'time' not in msg


def make_bot(mvp_list):
    settings = Settings(bot_user_token=None, database_url=None)
    return settings, mvp_list


def test_resolve_query_invalid_time_returns_error():
    import types

    class BotStub:
        settings = Settings(bot_user_token=None, database_url=None)

    channel_state = ChannelState(id_channel=1, id_guild=10, type=TrackType.MVP)
    results, mins_ago, error = _resolve_query(
        BotStub(), types.SimpleNamespace(timezone=None), channel_state, 'bafomé', '99x9'
    )
    assert results == [] and mins_ago == 0
    assert error == 'HHMM format expected for user time'
