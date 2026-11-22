from yellowtracker.domain.models import Mvp
from yellowtracker.domain.track_type import TrackType
from yellowtracker.service.entry_service import find_entry


class StubBot:
    def __init__(self, mvp_list):
        self.mvp_list = mvp_list
        self.mining_list = []


def make_bot(mvp_list):
    return StubBot(mvp_list)


MVP_LIST = [
    Mvp(id=1, name='Amon Ra', map='Subsolo da Pirâmide (2)', t1=60, t2=70, alias=['amon']),
    Mvp(id=2, name='Amon Ra do Pesadelo', map='Subsolo da Pirâmide (2) - Pesadelo',
        t1=60, t2=70, alias=['Nightmare Amon Ra']),
    Mvp(id=3, name='Bafomé', map='Labirinto da Floresta (3)', t1=120, t2=130, alias=['Baphomet']),
    Mvp(id=4, name='Atroce', map='Planície de Ida', t1=180, t2=190, alias=['Atroce Ida']),
    Mvp(id=5, name='Atroce', map='Pradaria Audhumbla', t1=300, t2=310, alias=['Atroce Audhumbla']),
]


def test_exact_match_returns_single():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'bafomé', TrackType.MVP) == [MVP_LIST[2]]


def test_exact_match_including_map():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'Atroce Pradaria Audhumbla', TrackType.MVP) == [MVP_LIST[4]]


def test_prefix_match_includes_map():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'amon ra subsolo da pirâmide (2)', TrackType.MVP) == [MVP_LIST[0]]


def test_prefix_match_returns_all_candidates():
    bot = make_bot(MVP_LIST)
    results = find_entry(bot, 'am', TrackType.MVP)
    assert {x.id for x in results} == {1, 2}


def test_alias_exact_match_short_circuits():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'baphomet', TrackType.MVP) == [MVP_LIST[2]]


def test_alias_prefix_match():
    bot = make_bot(MVP_LIST)
    results = find_entry(bot, 'nightmare', TrackType.MVP)
    assert [x.id for x in results] == [2]


def test_case_insensitive():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'AMON RA SUBSOLO DA PIRÂMIDE (2)', TrackType.MVP) == [MVP_LIST[0]]


def test_no_match_returns_empty():
    bot = make_bot(MVP_LIST)
    assert find_entry(bot, 'poring', TrackType.MVP) == []
