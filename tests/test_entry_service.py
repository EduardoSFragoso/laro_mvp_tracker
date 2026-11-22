from yellowtracker.domain.models import Mvp
from yellowtracker.service.entry_service import ac_entries, find_entry


class StubBot:
    def __init__(self, mvp_list):
        self.mvp_list = mvp_list


def make_bot(mvp_list):
    return StubBot(mvp_list)


MVP_LIST = [
    Mvp(id=1, name='Amon Ra', map='Subsolo da Pirâmide (2)', t1=60, t2=70, alias=['amon']),
    Mvp(
        id=2,
        name='Amon Ra do Pesadelo',
        map='Subsolo da Pirâmide (2) - Pesadelo',
        t1=60,
        t2=70,
        alias=['Nightmare Amon Ra'],
    ),
    Mvp(id=3, name='Bafomé', map='Labirinto da Floresta (3)', t1=120, t2=130, alias=['Baphomet']),
    Mvp(id=4, name='Atroce', map='Planície de Ida', t1=180, t2=190, alias=['Atroce Ida']),
    Mvp(id=5, name='Atroce', map='Pradaria Audhumbla', t1=300, t2=310, alias=['Atroce Audhumbla']),
]


def test_exact_match_returns_single():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'bafomé') == [MVP_LIST[2]]


def test_exact_match_including_map():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'Atroce Pradaria Audhumbla') == [MVP_LIST[4]]


def test_prefix_match_includes_map():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'amon ra subsolo da pirâmide (2)') == [MVP_LIST[0]]


def test_prefix_match_returns_all_candidates():
    bot = make_bot(MVP_LIST)
    results = find_entry(bot, 'am')
    assert {x.id for x in results} == {1, 2}


def test_alias_exact_match_short_circuits():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'baphomet') == [MVP_LIST[2]]


def test_alias_prefix_match():
    bot = make_bot(MVP_LIST)
    results = find_entry(bot, 'nightmare')
    assert [x.id for x in results] == [2]


def test_case_insensitive():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'AMON RA SUBSOLO DA PIRÂMIDE (2)') == [MVP_LIST[0]]


def test_no_match_returns_empty():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'poring') == []


def test_ac_entries_empty_query_returns_none():
    bot = make_bot(MVP_LIST)
    assert ac_entries(bot, '') == []


def test_ac_entries_prefix_includes_alias_and_name():
    bot = make_bot(MVP_LIST)
    names = [name for name, _map in ac_entries(bot, 'am')]
    assert names == ['Amon Ra', 'Amon Ra do Pesadelo']
    names = [name for name, _map in ac_entries(bot, 'baphomet')]
    assert names == ['Bafomé']


def test_ac_entries_deduplicates_by_name_with_map_hint():
    bot = make_bot(MVP_LIST)
    entries = ac_entries(bot, 'atroce')
    assert len(entries) == 2
    assert {label for label, _value in entries} == {'Atroce (Planície de Ida)', 'Atroce (Pradaria Audhumbla)'}
    values = {value for _label, value in entries}
    assert {find_entry(bot, v)[0].id for v in values} == {4, 5}
