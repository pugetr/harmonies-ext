from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TerrainColor(str, Enum):
    WATER = "water"
    MOUNTAIN = "mountain"
    WOOD = "wood"
    LEAF = "leaf"
    FIELD = "field"
    BUILDING = "building"


class BoardSide(str, Enum):
    A = "A"
    B = "B"


@dataclass(frozen=True, order=True)
class Coordinate:
    q: int
    r: int

    def __add__(self, other: Coordinate) -> Coordinate:
        return Coordinate(self.q + other.q, self.r + other.r)

    def neighbors(self) -> tuple[Coordinate, ...]:
        return tuple(self + direction for direction in HEX_DIRECTIONS)


HEX_DIRECTIONS: tuple[Coordinate, ...] = (
    Coordinate(1, 0),
    Coordinate(1, -1),
    Coordinate(0, -1),
    Coordinate(-1, 0),
    Coordinate(-1, 1),
    Coordinate(0, 1),
)


def rotate_clockwise(offset: Coordinate, steps: int) -> Coordinate:
    rotated = offset
    for _ in range(steps % 6):
        rotated = Coordinate(-rotated.r, rotated.q + rotated.r)
    return rotated


def make_hexagon(radius: int) -> frozenset[Coordinate]:
    if radius < 0:
        raise ValueError("radius must be non-negative")

    spaces: set[Coordinate] = set()
    for q in range(-radius, radius + 1):
        r_min = max(-radius, -q - radius)
        r_max = min(radius, -q + radius)
        for r in range(r_min, r_max + 1):
            spaces.add(Coordinate(q, r))
    return frozenset(spaces)
