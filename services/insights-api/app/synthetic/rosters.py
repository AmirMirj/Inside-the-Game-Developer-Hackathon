"""Synthetic club rosters for Northbridge FC vs Harbor FC."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    player_id: str
    team_id: str
    name: str
    number: int


@dataclass(frozen=True)
class Team:
    team_id: str
    name: str
    players: tuple[Player, ...]


NORTHBRIDGE = Team(
    team_id="northbridge",
    name="Northbridge FC",
    players=(
        Player("nb-1", "northbridge", "C. Hale", 1),
        Player("nb-2", "northbridge", "T. Ngoma", 2),
        Player("nb-4", "northbridge", "S. Dietrich", 4),
        Player("nb-6", "northbridge", "R. Patel", 6),
        Player("nb-7", "northbridge", "A. Reed", 7),
        Player("nb-8", "northbridge", "I. Moreau", 8),
        Player("nb-9", "northbridge", "M. Okonkwo", 9),
        Player("nb-10", "northbridge", "J. Silva", 10),
        Player("nb-11", "northbridge", "K. Byrne", 11),
        Player("nb-14", "northbridge", "E. Frost", 14),
        Player("nb-21", "northbridge", "P. Alvarez", 21),
    ),
)

HARBOR = Team(
    team_id="harbor",
    name="Harbor FC",
    players=(
        Player("hb-1", "harbor", "N. Berg", 1),
        Player("hb-3", "harbor", "D. Okoro", 3),
        Player("hb-4", "harbor", "J. Klein", 4),
        Player("hb-5", "harbor", "M. Rossi", 5),
        Player("hb-6", "harbor", "A. Novak", 6),
        Player("hb-7", "harbor", "Y. Chen", 7),
        Player("hb-8", "harbor", "F. Duarte", 8),
        Player("hb-9", "harbor", "B. Cole", 9),
        Player("hb-10", "harbor", "L. Vargas", 10),
        Player("hb-11", "harbor", "H. Ibrahim", 11),
        Player("hb-18", "harbor", "S. Quinn", 18),
    ),
)

MATCH_META = {
    "match_id": "syn-northbridge-harbor-half1",
    "label": "Northbridge FC vs Harbor FC — synthetic first half",
    "competition": "Synthetic Premier Showcase",
    "venue": "Northbridge Arena",
    "synthetic": True,
    "period": 1,
    "half_minutes": 45,
}
