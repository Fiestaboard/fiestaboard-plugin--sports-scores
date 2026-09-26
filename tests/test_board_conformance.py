"""Board-geometry conformance for the Sports Scores plugin.

Exercises the plugin against every board shape FiestaBoard supports (Flagship,
Note, and note-arrays from 15x3 up to 120x24 -- what a FiestaPanel is) using
the shared conformance suite core holds its own plugins to.
"""

import json
from pathlib import Path
from unittest.mock import Mock

from plugins.sports_scores import SportsScoresPlugin
from src.plugins.geometry_conformance import assert_board_conformance

MANIFEST = json.loads((Path(__file__).parent.parent / "manifest.json").read_text())

# Enough raw games (5 sports x 10 max each) that no geometry in the standard
# matrix -- including the 120x24 max array and the 15x24 growth-ladder rung,
# both of which need 23 body rows -- runs out of content before it runs out
# of board.
_EVENTS_PER_SPORT = 20


def _many_events(n: int) -> dict:
    return {
        "event": [
            {
                "strEvent": f"Home {i} vs Away {i}",
                "strHomeTeam": f"Home Team {i}",
                "strAwayTeam": f"Away Team {i}",
                "intHomeScore": str(10 + i),
                "intAwayScore": str(i),
                "strStatus": "Match Finished",
                "dateEvent": "2024-01-15",
                "strTime": "20:00:00",
            }
            for i in range(n)
        ]
    }


def make_plugin_factory(monkeypatch):
    """A `make_plugin` factory (per the shared suite's contract) with the
    network stubbed and the plugin's own inter-sport delay disabled so the
    many renders the suite performs stay fast.
    """

    def make_plugin() -> SportsScoresPlugin:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = _many_events(_EVENTS_PER_SPORT)
        mock_response.text = json.dumps(_many_events(1))
        monkeypatch.setattr(
            "plugins.sports_scores.requests.get",
            Mock(return_value=mock_response),
        )
        monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

        plugin = SportsScoresPlugin(MANIFEST)
        plugin.config = {
            "enabled": True,
            "sports": ["NFL", "Soccer", "NHL", "NBA", "MLB"],
            "api_key": "",
            "refresh_seconds": 300,
            "max_games_per_sport": 10,
        }
        return plugin

    return make_plugin


def test_renders_on_every_board_shape(monkeypatch):
    assert_board_conformance(
        make_plugin_factory(monkeypatch),
        manifest=MANIFEST,
        strict_growth=True,
        require_note_array_preview=True,
    )
