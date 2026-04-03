from harmonies.board import PlayerBoard
from harmonies.cards import AnimalCardDefinition, AnimalCardState, HabitatPattern, StackRequirement
from harmonies.model import BoardSide, Coordinate, TerrainColor, make_hexagon
from harmonies.scoring import score_breakdown, score_buildings, score_fields, score_mountains, score_rivers, score_trees, score_water


def board(side: BoardSide = BoardSide.A) -> PlayerBoard:
    return PlayerBoard(side=side, spaces=make_hexagon(3))


def test_tree_scoring_uses_1_3_7_values() -> None:
    game_board = board()
    game_board = game_board.place_token(TerrainColor.LEAF, Coordinate(0, 0))
    game_board = game_board.place_token(TerrainColor.WOOD, Coordinate(1, 0))
    game_board = game_board.place_token(TerrainColor.LEAF, Coordinate(1, 0))
    game_board = game_board.place_token(TerrainColor.WOOD, Coordinate(2, 0))
    game_board = game_board.place_token(TerrainColor.WOOD, Coordinate(2, 0))
    game_board = game_board.place_token(TerrainColor.LEAF, Coordinate(2, 0))

    assert score_trees(game_board) == 11


def test_isolated_mountains_score_zero() -> None:
    game_board = board()
    game_board = game_board.place_token(TerrainColor.MOUNTAIN, Coordinate(0, 0))
    game_board = game_board.place_token(TerrainColor.MOUNTAIN, Coordinate(2, 0))

    assert score_mountains(game_board) == 0


def test_adjacent_mountains_score_by_height() -> None:
    game_board = board()
    game_board = game_board.place_token(TerrainColor.MOUNTAIN, Coordinate(0, 0))
    game_board = game_board.place_token(TerrainColor.MOUNTAIN, Coordinate(1, 0))
    game_board = game_board.place_token(TerrainColor.MOUNTAIN, Coordinate(1, 0))

    assert score_mountains(game_board) == 4


def test_fields_score_per_group_of_two_or_more() -> None:
    game_board = board()
    game_board = game_board.place_token(TerrainColor.FIELD, Coordinate(0, 0))
    game_board = game_board.place_token(TerrainColor.FIELD, Coordinate(1, 0))
    game_board = game_board.place_token(TerrainColor.FIELD, Coordinate(-2, 0))

    assert score_fields(game_board) == 5


def test_river_scoring_uses_longest_shortest_path() -> None:
    game_board = board(BoardSide.A)
    for coordinate in [
        Coordinate(0, 0),
        Coordinate(1, 0),
        Coordinate(2, 0),
        Coordinate(3, 0),
    ]:
        game_board = game_board.place_token(TerrainColor.WATER, coordinate)

    assert score_rivers(game_board) == 8


def test_islands_score_on_side_b() -> None:
    game_board = board(BoardSide.B)
    for coordinate in [
        Coordinate(0, -3),
        Coordinate(0, -2),
        Coordinate(0, -1),
        Coordinate(0, 0),
        Coordinate(0, 1),
        Coordinate(0, 2),
        Coordinate(0, 3),
    ]:
        game_board = game_board.place_token(TerrainColor.WATER, coordinate)

    assert score_water(game_board) == 10


def test_buildings_need_three_neighbor_colors() -> None:
    game_board = board()
    game_board = game_board.place_token(TerrainColor.MOUNTAIN, Coordinate(0, 0))
    game_board = game_board.place_token(TerrainColor.BUILDING, Coordinate(0, 0))
    game_board = game_board.place_token(TerrainColor.FIELD, Coordinate(1, 0))
    game_board = game_board.place_token(TerrainColor.WATER, Coordinate(1, -1))
    game_board = game_board.place_token(TerrainColor.WOOD, Coordinate(0, -1))

    assert score_buildings(game_board) == 5


def test_animal_cards_score_highest_uncovered_value_only() -> None:
    pattern = HabitatPattern(
        requirements={Coordinate(0, 0): StackRequirement(top=TerrainColor.FIELD, height=1)},
        target_offset=Coordinate(0, 0),
    )
    card = AnimalCardDefinition(
        card_id="hare",
        name="Hare",
        habitat=pattern,
        points_by_cubes_placed=(0, 4, 9),
    )
    game_board = board().place_token(TerrainColor.FIELD, Coordinate(0, 0))

    breakdown = score_breakdown(game_board, (AnimalCardState(card, cubes_placed=1),))
    assert breakdown.animals == 4
