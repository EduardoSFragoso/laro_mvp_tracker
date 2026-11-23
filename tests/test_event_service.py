from datetime import datetime
from typing import cast

from laro.config import Settings
from laro.domain.bot import Bot
from laro.service import event_service


def stub_bot(timezone='America/Sao_Paulo'):
    class StubBot:
        settings = Settings(bot_user_token=None, database_url=None, timezone=timezone)

    return cast(Bot, StubBot())


def sunday_night(hour=22, minute=30):
    # Domingo 2026-11-22, depois do fim da WoE (20:00-22:00): o servidor
    # não tem mais nenhum evento nesta semana, então o próximo deve ser o
    # da semana seguinte (domingo 7 dias depois).
    return datetime(2026, 11, 22, hour, minute)


def localized(dt):
    from pytz import timezone

    return timezone('America/Sao_Paulo').localize(dt, is_dst=False)


def test_get_evts_woe_returns_sorted_events():
    bot = stub_bot()
    evts = event_service.get_evts(bot, type='woe')
    assert len(evts) > 0
    assert all(e['type'] == 'woe' for e in evts)
    begins = [e['dt_begin'] for e in evts]
    assert begins == sorted(begins)


def test_woe_evt_is_sunday_20h_to_22h():
    bot = stub_bot()
    evts = event_service.get_evts(bot, type='woe')
    # WoE oficial do LATAM: domingo (weekday 7) 20:00-22:00
    assert len(evts) == 1
    assert str(evts[0]['weekday']) == '7'
    assert str(evts[0]['begin']) == '20:00'
    assert str(evts[0]['end']) == '22:00'
    assert evts[0]['dt_end'] > evts[0]['dt_begin']


def test_get_next_evt_returns_event():
    bot = stub_bot()
    evt, ongoing = event_service.get_next_evt(bot, type='woe')
    assert evt is not None
    assert 'name' in evt and 'dt_begin' in evt and 'dt_end' in evt


def test_get_next_evt_sunday_after_woe_finds_next_week():
    # Bug de fim de semana: entre domingo 22:00 e 24:00 a WoE desta semana
    # já terminou; o serviço congelado nesse horário precisa achar a WoE da
    # semana seguinte em vez de responder vazio.
    bot = stub_bot()
    evt, ongoing = event_service.get_next_evt(bot, type='woe', dt_now=sunday_night())
    assert evt is not None, 'deveria achar a WoE da semana seguinte'
    assert ongoing is False
    assert evt['dt_begin'] > localized(sunday_night())
    assert evt['dt_begin'].isoweekday() == 7


def test_get_next_evt_sunday_during_woe_is_ongoing():
    # Domingo 21:00, dentro da janela: continua marcando como ongoing.
    bot = stub_bot()
    evt, ongoing = event_service.get_next_evt(bot, type='woe', dt_now=sunday_night(21, 0))
    assert evt is not None
    assert ongoing is True
    assert localized(sunday_night(21, 0)) <= evt['dt_end']
    assert evt['dt_begin'] <= localized(sunday_night(21, 0))


def test_get_next_evt_unknown_type_returns_none():
    # Tipo de evento inexistente no LATAM: a lista está vazia e o serviço
    # deve responder graciosamente em vez de quebrar.
    bot = stub_bot()
    evt, ongoing = event_service.get_next_evt(bot, type='inexistente')
    assert evt is None
    assert ongoing is False


def test_woe_map_handles_empty_ok():
    bot = stub_bot()
    woe_map = event_service.get_woe_map(bot)
    assert woe_map['next'] != ''
    assert woe_map['sunday'] != '' and woe_map['sunday'] != '\n'
    assert 'WoE' in woe_map['sunday']
