from __future__ import annotations

from dataclasses import dataclass

from harmonies.board import PlayerBoard
from harmonies.model import Coordinate


CELL_WIDTH = 6
ROW_HEIGHT = 2


@dataclass(frozen=True)
class BoardPosition:
    row: int
    column: int


@dataclass(frozen=True)
class BoardLayout:
    positions: dict[Coordinate, BoardPosition]

    def position_for(self, coordinate: Coordinate) -> BoardPosition:
        return self.positions[coordinate]

    def move_left(self, board: PlayerBoard, coordinate: Coordinate) -> Coordinate:
        return self._move_horizontal(board, coordinate, delta=-1)

    def move_right(self, board: PlayerBoard, coordinate: Coordinate) -> Coordinate:
        return self._move_horizontal(board, coordinate, delta=1)

    def move_up(self, board: PlayerBoard, coordinate: Coordinate) -> Coordinate:
        return self._move_vertical(board, coordinate, direction=-1)

    def move_down(self, board: PlayerBoard, coordinate: Coordinate) -> Coordinate:
        return self._move_vertical(board, coordinate, direction=1)

    def _move_horizontal(self, board: PlayerBoard, coordinate: Coordinate, delta: int) -> Coordinate:
        target = Coordinate(coordinate.q + delta, coordinate.r)
        if target in board.spaces:
            return target
        return coordinate

    def _move_vertical(self, board: PlayerBoard, coordinate: Coordinate, direction: int) -> Coordinate:
        source = self.position_for(coordinate)
        candidate_positions = []
        for neighbor in coordinate.neighbors():
            if neighbor not in board.spaces:
                continue
            target = self.position_for(neighbor)
            if direction < 0 and target.row < source.row:
                candidate_positions.append((abs(target.column - source.column), target.column, neighbor))
            elif direction > 0 and target.row > source.row:
                candidate_positions.append((abs(target.column - source.column), target.column, neighbor))

        if not candidate_positions:
            return coordinate
        return min(candidate_positions)[2]


def build_board_layout(board: PlayerBoard) -> BoardLayout:
    rows = []
    for row_index, axis_r in enumerate(range(-3, 4)):
        coordinates = sorted(coordinate for coordinate in board.spaces if coordinate.r == axis_r)
        indent = abs(axis_r) * (CELL_WIDTH // 2)
        for column_index, coordinate in enumerate(coordinates):
            rows.append(
                (
                    coordinate,
                    BoardPosition(
                        row=row_index * ROW_HEIGHT,
                        column=indent + column_index * CELL_WIDTH,
                    ),
                )
            )
    return BoardLayout(positions=dict(rows))