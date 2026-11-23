from datetime import UTC, datetime, timedelta
from typing import cast

import discord

from laro.config import Settings
from laro.domain.bot import Bot
from laro.domain.models import ChannelState
from laro.domain.track_type import TrackType
from laro.service import channel_service
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
        cast(Bot, BotStub()), types.SimpleNamespace(timezone=None), channel_state, 'bafomé', '99x9'
    )
    assert results == [] and mins_ago == 0
    assert error == 'HHMM format expected for user time'


def _msg_stub(msg_id, created_at, edited_at=None):
    import types

    # is_msg_can_be_deleted só usa id/created_at/edited_at; o cast deixa isso explícito.
    return cast(discord.Message, types.SimpleNamespace(id=msg_id, created_at=created_at, edited_at=edited_at))


def _bot_stub():
    class BotStub:
        settings = Settings(bot_user_token=None, database_url=None)

    return cast(Bot, BotStub())


def make_channel_state(msg_id=None):
    return ChannelState(
        id_channel=1,
        id_guild=10,
        type=TrackType.MVP,
        id_message=msg_id,
        id_help_message=None,
        notification_message=None,
    )


def _dt_ago(**kwargs):
    return datetime.now(UTC) - timedelta(**kwargs)


def test_msg_dentro_da_janela_nao_apaga():
    msg = _msg_stub(100, _dt_ago(seconds=2))
    # a mensagem só é candidata a apagar depois de viver DEL_MSG_AFTER_SECS (10s)
    assert channel_service.is_msg_can_be_deleted(_bot_stub(), make_channel_state(msg_id=999), msg) is False


def test_msg_velha_fora_da_janela_pode_apagar():
    msg = _msg_stub(100, _dt_ago(seconds=60))
    assert channel_service.is_msg_can_be_deleted(_bot_stub(), make_channel_state(msg_id=999), msg) is True


def test_msg_com_14_dias_e_protegida():
    msg = _msg_stub(100, _dt_ago(days=20))
    # regra de segurança: >=14 dias nunca apaga (mesmo fora da janela)
    assert channel_service.is_msg_can_be_deleted(_bot_stub(), make_channel_state(msg_id=999), msg) is False


def test_msg_editada_recente_nao_apaga():
    # criada há 60s (fora da janela) mas editada há 2s (dentro): janela reinicia
    msg = _msg_stub(100, _dt_ago(seconds=60), edited_at=_dt_ago(seconds=2))
    assert channel_service.is_msg_can_be_deleted(_bot_stub(), make_channel_state(msg_id=999), msg) is False


def test_msg_da_tabela_nao_apaga():
    msg = _msg_stub(100, datetime(2026, 1, 1, tzinfo=UTC))
    # mensagem apontada como tabela/ajuda do canal é protegida, sem exceção
    assert channel_service.is_msg_can_be_deleted(_bot_stub(), make_channel_state(msg_id=100), msg) is False
