from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from harmonies.board import MOUNTAIN_SCORES, TREE_SCORES, PlayerBoard
from harmonies.cards import AnimalCardState
from harmonies.model import BoardSide, Coordinate, TerrainColor


@dataclass(frozen=True)
class ScoreBreakdown:
    trees: int
    mountains: int
    fields: int
    water: int
    buildings: int
    animals: int

    @property
    def total(self) -> int:
        return self.trees + self.mountains + self.fields + self.water + self.buildings + self.animals


def score_player_board(board: PlayerBoard) -> tuple[int, int, int, int, int]:
    trees = score_trees(board)
    mountains = score_mountains(board)
    fields = score_fields(board)
    water = score_water(board)
    buildings = score_buildings(board)
    return trees, mountains, fields, water, buildings


def score_animal_cards(cards: tuple[AnimalCardState, ...]) -> int:
    return sum(card.score() for card in cards)


def score_breakdown(board: PlayerBoard, cards: tuple[AnimalCardState, ...]) -> ScoreBreakdown:
    trees, mountains, fields, water, buildings = score_player_board(board)
    animals = score_animal_cards(cards)
    return ScoreBreakdown(
        trees=trees,
        mountains=mountains,
        fields=fields,
        water=water,
        buildings=buildings,
        animals=animals,
    )


def score_trees(board: PlayerBoard) -> int:
    total = 0
    for coordinate in board.occupied_spaces():
        if board.is_tree(coordinate):
            total += TREE_SCORES[len(board.cell(coordinate).tokens)]
    return total


def score_mountains(board: PlayerBoard) -> int:
    total = 0
    for coordinate in board.occupied_spaces():
        if not board.is_mountain(coordinate):
            continue

        if any(board.is_mountain(neighbor) for neighbor in coordinate.neighbors() if neighbor in board.spaces):
            total += MOUNTAIN_SCORES[len(board.cell(coordinate).tokens)]
    return total


def score_fields(board: PlayerBoard) -> int:
    groups = _connected_components(board, lambda coordinate: board.is_field(coordinate), board.occupied_spaces())
    return sum(5 for group in groups if len(group) >= 2)


def score_water(board: PlayerBoard) -> int:
    if board.side == BoardSide.A:
        return score_rivers(board)
    return score_islands(board)


def score_rivers(board: PlayerBoard) -> int:
    components = _connected_components(board, lambda coordinate: board.is_water(coordinate), board.occupied_spaces())
    best_length = 0
    for component in components:
        best_length = max(best_length, _component_diameter(board, component))
    return _river_points(best_length)


def score_islands(board: PlayerBoard) -> int:
    islands = _connected_components(board, lambda coordinate: not board.is_water(coordinate), board.spaces)
    return 5 * len(islands)


def score_buildings(board: PlayerBoard) -> int:
    total = 0
    for coordinate in board.occupied_spaces():
        if not board.is_building(coordinate):
            continue

        neighbor_colors = {
            board.top_color(neighbor)
            for neighbor in coordinate.neighbors()
            if neighbor in board.spaces and board.top_color(neighbor) is not None
        }
        if len(neighbor_colors) >= 3:
            total += 5
    return total


def _river_points(length: int) -> int:
    if length <= 1:
        return 0
    if length == 2:
        return 2
    if length == 3:
        return 5
    if length == 4:
        return 8
    if length == 5:
        return 11
    if length == 6:
        return 15
    return 15 + 4 * (length - 6)


def _component_diameter(board: PlayerBoard, component: frozenset[Coordinate]) -> int:
    best = 0
    for start in component:
        distances = _shortest_paths(board, start, component)
        best = max(best, max(distances.values(), default=0) + 1)
    return best


def _shortest_paths(
    board: PlayerBoard,
    start: Coordinate,
    component: frozenset[Coordinate],
) -> dict[Coordinate, int]:
    queue: deque[Coordinate] = deque([start])
    distances = {start: 0}

    while queue:
        current = queue.popleft()
        for neighbor in current.neighbors():
            if neighbor not in component or neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def _connected_components(
    board: PlayerBoard,
    predicate,
    coordinates: frozenset[Coordinate],
) -> tuple[frozenset[Coordinate], ...]:
    matching = {coordinate for coordinate in coordinates if predicate(coordinate)}
    seen: set[Coordinate] = set()
    components: list[frozenset[Coordinate]] = []

    for coordinate in matching:
        if coordinate in seen:
            continue
        queue: deque[Coordinate] = deque([coordinate])
        component: set[Coordinate] = set()
        seen.add(coordinate)

        while queue:
            current = queue.popleft()
            component.add(current)
            for neighbor in current.neighbors():
                if neighbor in matching and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

        components.append(frozenset(component))

    return tuple(components)
