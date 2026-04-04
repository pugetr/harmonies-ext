from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from harmonies.model import BoardSide, Coordinate, TerrainColor, make_hexagon


TREE_SCORES = {1: 1, 2: 3, 3: 7}
MOUNTAIN_SCORES = {1: 1, 2: 3, 3: 7}


OFFICIAL_BOARD_SPACES: frozenset[Coordinate] = make_hexagon(3)
OFFICIAL_BOARD_LAYOUTS: dict[BoardSide, frozenset[Coordinate]] = {
    BoardSide.A: OFFICIAL_BOARD_SPACES,
    BoardSide.B: OFFICIAL_BOARD_SPACES,
}


@dataclass(frozen=True)
class CellState:
    tokens: tuple[TerrainColor, ...] = ()
    cube_marker: Optional[str] = None

    @property
    def height(self) -> int:
        return len(self.tokens)

    @property
    def top_color(self) -> Optional[TerrainColor]:
        return self.tokens[-1] if self.tokens else None


@dataclass(frozen=True)
class PlayerBoard:
    side: BoardSide
    spaces: frozenset[Coordinate]
    cells: dict[Coordinate, CellState] = field(default_factory=dict)

    def cell(self, coordinate: Coordinate) -> CellState:
        self._assert_space(coordinate)
        return self.cells.get(coordinate, CellState())

    def empty_space_count(self) -> int:
        return sum(1 for coordinate in self.spaces if not self.cell(coordinate).tokens)

    def top_color(self, coordinate: Coordinate) -> Optional[TerrainColor]:
        return self.cell(coordinate).top_color

    def place_token(self, color: TerrainColor, coordinate: Coordinate) -> PlayerBoard:
        self._assert_space(coordinate)
        current = self.cell(coordinate)

        if current.cube_marker is not None:
            raise ValueError("cannot place a token on a space with an animal cube")

        tokens = current.tokens
        if len(tokens) >= 3:
            raise ValueError("stacks cannot exceed height 3")

        if color in {TerrainColor.WATER, TerrainColor.FIELD}:
            if tokens:
                raise ValueError("water and field tokens can only be placed on empty spaces")
        elif color == TerrainColor.MOUNTAIN:
            if tokens and (set(tokens) != {TerrainColor.MOUNTAIN} or len(tokens) >= 3):
                raise ValueError("mountains can only stack on mountains up to height 3")
        elif color == TerrainColor.WOOD:
            if tokens and (set(tokens) != {TerrainColor.WOOD} or len(tokens) >= 2):
                raise ValueError("wood tokens can only stack on wood up to height 2")
        elif color == TerrainColor.LEAF:
            if tokens and (set(tokens) != {TerrainColor.WOOD} or len(tokens) not in {1, 2}):
                raise ValueError("leaf tokens can only be placed on empty spaces or on 1-2 wood tokens")
            if tokens and len(tokens) == 3:
                raise ValueError("trees cannot exceed height 3")
        elif color == TerrainColor.BUILDING:
            if len(tokens) != 1 or tokens[0] not in {
                TerrainColor.MOUNTAIN,
                TerrainColor.WOOD,
                TerrainColor.BUILDING,
            }:
                raise ValueError("buildings must be placed on a single mountain, wood, or building token")
        else:
            raise ValueError(f"unsupported terrain color: {color}")

        updated_cells = dict(self.cells)
        updated_cells[coordinate] = CellState(tokens=tokens + (color,), cube_marker=current.cube_marker)
        return replace(self, cells=updated_cells)

    def place_cube(self, coordinate: Coordinate, cube_marker: str) -> PlayerBoard:
        self._assert_space(coordinate)
        current = self.cell(coordinate)
        if not current.tokens:
            raise ValueError("cannot place an animal cube on an empty space")
        if current.cube_marker is not None:
            raise ValueError("only one animal cube may occupy a space")

        updated_cells = dict(self.cells)
        updated_cells[coordinate] = CellState(tokens=current.tokens, cube_marker=cube_marker)
        return replace(self, cells=updated_cells)

    def is_tree(self, coordinate: Coordinate) -> bool:
        tokens = self.cell(coordinate).tokens
        if not tokens or tokens[-1] != TerrainColor.LEAF:
            return False
        return all(token == TerrainColor.WOOD for token in tokens[:-1])

    def is_mountain(self, coordinate: Coordinate) -> bool:
        tokens = self.cell(coordinate).tokens
        return bool(tokens) and all(token == TerrainColor.MOUNTAIN for token in tokens)

    def is_field(self, coordinate: Coordinate) -> bool:
        return self.cell(coordinate).top_color == TerrainColor.FIELD

    def is_water(self, coordinate: Coordinate) -> bool:
        return self.cell(coordinate).top_color == TerrainColor.WATER

    def is_building(self, coordinate: Coordinate) -> bool:
        tokens = self.cell(coordinate).tokens
        return (
            len(tokens) == 2
            and tokens[-1] == TerrainColor.BUILDING
            and tokens[0] in {TerrainColor.MOUNTAIN, TerrainColor.WOOD, TerrainColor.BUILDING}
        )

    def occupied_spaces(self) -> frozenset[Coordinate]:
        return frozenset(coordinate for coordinate in self.spaces if self.cell(coordinate).tokens)

    def _assert_space(self, coordinate: Coordinate) -> None:
        if coordinate not in self.spaces:
            raise ValueError(f"coordinate {coordinate} is outside the board layout")


def board_spaces_for_side(side: BoardSide) -> frozenset[Coordinate]:
    try:
        return OFFICIAL_BOARD_LAYOUTS[side]
    except KeyError as error:
        raise ValueError(f"unsupported board side: {side}") from error


def create_player_board(side: BoardSide) -> PlayerBoard:
    return PlayerBoard(side=side, spaces=board_spaces_for_side(side))
