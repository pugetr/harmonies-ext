from harmonies.board import PlayerBoard
from harmonies.model import BoardSide, Coordinate, TerrainColor, make_hexagon


def build_board() -> PlayerBoard:
    return PlayerBoard(side=BoardSide.A, spaces=make_hexagon(2))


def test_green_can_be_placed_on_empty_or_wood_stacks() -> None:
    board = build_board()
    board = board.place_token(TerrainColor.LEAF, Coordinate(0, 0))
    board = board.place_token(TerrainColor.WOOD, Coordinate(1, 0))
    board = board.place_token(TerrainColor.LEAF, Coordinate(1, 0))

    assert board.cell(Coordinate(0, 0)).tokens == (TerrainColor.LEAF,)
    assert board.cell(Coordinate(1, 0)).tokens == (TerrainColor.WOOD, TerrainColor.LEAF)


def test_water_cannot_be_stacked() -> None:
    board = build_board().place_token(TerrainColor.WOOD, Coordinate(0, 0))

    try:
        board.place_token(TerrainColor.WATER, Coordinate(0, 0))
    except ValueError as error:
        assert "empty spaces" in str(error)
    else:
        raise AssertionError("expected water placement on a stack to fail")


def test_red_must_be_second_token_on_legal_base() -> None:
    board = build_board().place_token(TerrainColor.MOUNTAIN, Coordinate(0, 0))
    board = board.place_token(TerrainColor.BUILDING, Coordinate(0, 0))

    assert board.cell(Coordinate(0, 0)).tokens == (TerrainColor.MOUNTAIN, TerrainColor.BUILDING)


def test_token_cannot_be_placed_on_space_with_cube() -> None:
    board = build_board().place_token(TerrainColor.FIELD, Coordinate(0, 0))
    board = board.place_cube(Coordinate(0, 0), "fox:1")

    try:
        board.place_token(TerrainColor.FIELD, Coordinate(0, 0))
    except ValueError as error:
        assert "animal cube" in str(error)
    else:
        raise AssertionError("expected token placement on a cube space to fail")
