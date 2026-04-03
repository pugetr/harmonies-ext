from __future__ import annotations

from dataclasses import dataclass

from harmonies.board import PlayerBoard
from harmonies.model import Coordinate, TerrainColor, rotate_clockwise


@dataclass(frozen=True)
class StackRequirement:
    top: TerrainColor
    height: int
    building_base_allowed: tuple[TerrainColor, ...] = ()

    def matches(self, tokens: tuple[TerrainColor, ...]) -> bool:
        if len(tokens) != self.height:
            return False
        if not tokens or tokens[-1] != self.top:
            return False
        if self.top == TerrainColor.BUILDING:
            return len(tokens) == 2 and tokens[0] in set(self.building_base_allowed)
        return True


@dataclass(frozen=True)
class HabitatPattern:
    requirements: dict[Coordinate, StackRequirement]
    target_offset: Coordinate

    def rotated_requirements(self, rotation: int) -> dict[Coordinate, StackRequirement]:
        return {
            rotate_clockwise(offset, rotation): requirement
            for offset, requirement in self.requirements.items()
        }

    def rotated_target(self, rotation: int) -> Coordinate:
        return rotate_clockwise(self.target_offset, rotation)


@dataclass(frozen=True)
class AnimalCardDefinition:
    card_id: str
    name: str
    habitat: HabitatPattern
    points_by_cubes_placed: tuple[int, ...]

    @property
    def cube_count(self) -> int:
        return len(self.points_by_cubes_placed) - 1

    def score_for(self, cubes_placed: int) -> int:
        if cubes_placed < 0 or cubes_placed > self.cube_count:
            raise ValueError("cubes_placed is outside the score ladder")
        return self.points_by_cubes_placed[cubes_placed]


@dataclass(frozen=True)
class AnimalCardState:
    definition: AnimalCardDefinition
    cubes_placed: int = 0

    @property
    def complete(self) -> bool:
        return self.cubes_placed == self.definition.cube_count

    def place_cube(self) -> AnimalCardState:
        if self.complete:
            raise ValueError("all cubes for this animal card are already placed")
        return AnimalCardState(definition=self.definition, cubes_placed=self.cubes_placed + 1)

    def score(self) -> int:
        return self.definition.score_for(self.cubes_placed)


def resolve_habitat_target(
    board: PlayerBoard,
    pattern: HabitatPattern,
    anchor: Coordinate,
    rotation: int,
) -> Coordinate:
    rotated_requirements = pattern.rotated_requirements(rotation)
    rotated_target = pattern.rotated_target(rotation)

    for offset, requirement in rotated_requirements.items():
        coordinate = anchor + offset
        tokens = board.cell(coordinate).tokens
        if not requirement.matches(tokens):
            raise ValueError("board state does not match the habitat pattern")

    target_coordinate = anchor + rotated_target
    if board.cell(target_coordinate).cube_marker is not None:
        raise ValueError("the habitat target already contains an animal cube")
    return target_coordinate
