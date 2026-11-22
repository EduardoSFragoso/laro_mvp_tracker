from yellowtracker.config import Settings
from yellowtracker.service import event_service


def stub_bot(timezone='America/Sao_Paulo'):
    class StubBot:
        settings = Settings(bot_user_token=None, database_url=None, timezone=timezone)

    return StubBot()


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


def test_get_next_evt_empty_type_returns_none():
    # GMC e Happy Hour não existem no LATAM: a lista está vazia e o serviço
    # deve responder graciosamente em vez de quebrar.
    bot = stub_bot()
    evt, ongoing = event_service.get_next_evt(bot, type='gmc')
    assert evt is None
    assert ongoing is False


def test_woe_map_handles_empty_ok():
    bot = stub_bot()
    woe_map = event_service.get_woe_map(bot)
    assert woe_map['next'] != ''
    assert woe_map['sunday'] != '' and woe_map['sunday'] != '\n'
    assert 'WoE' in woe_map['sunday']


def test_gmc_map_empty_is_graceful():
    bot = stub_bot()
    gmc_map = event_service.get_gmc_map(bot)
    assert gmc_map['ongoing'] == ''
    assert gmc_map['next']  # placeholder dentro do mapa
    assert gmc_map['next'] != '\n'
