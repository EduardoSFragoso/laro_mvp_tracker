from __future__ import annotations

import pytest

from laro.event.on_message import _split_track_args


@pytest.mark.parametrize(
    ('args', 'expected'),
    [
        ([], (None, None)),
        (['Serpente', 'Suprema'], ('Serpente Suprema', None)),
        (['Serpente', 'Suprema', '2035'], ('Serpente Suprema', '2035')),
        (['Serpente', 'Suprema', '20:35'], ('Serpente Suprema', '2035')),
        (['amon', 'ra', '0810'], ('amon ra', '0810')),
        (['atroce'], ('atroce', None)),
    ],
)
def test_split_track_args(args: list[str], expected: tuple[str | None, str | None]) -> None:
    assert _split_track_args(args) == expected
