from harmonies.cards import AnimalCardDefinition, HabitatPattern, StackRequirement
from harmonies.game import GameRules
from harmonies.model import BoardSide, Coordinate, TerrainColor
from harmonies.ui import GameController, build_board_layout, render_board, render_game_summary
from harmonies.ui.app import handle_command, parse_coordinate, render_screen


def simple_card(card_id: str = "meerkat") -> AnimalCardDefinition:
    return AnimalCardDefinition(
        card_id=card_id,
        name=card_id.title(),
        habitat=HabitatPattern(
            requirements={
                Coordinate(0, 0): StackRequirement(top=TerrainColor.MOUNTAIN, height=1),
                Coordinate(1, 0): StackRequirement(top=TerrainColor.FIELD, height=1),
            },
            target_offset=Coordinate(0, 0),
        ),
        points_by_cubes_placed=(0, 4, 8),
    )


def build_state():
    cards = tuple(simple_card(f"card-{index}") for index in range(8))
    bag = (
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
    )
    return GameRules.create_game(
        player_count=2,
        board_side=BoardSide.A,
        bag=bag,
        animal_deck=cards,
    )


def test_controller_reports_available_offers_and_legal_token_coordinates() -> None:
    controller = GameController(build_state())

    assert len(controller.available_offers()) == 5
    assert controller.legal_token_coordinates() == ()

    error = controller.draft_offer(0)

    assert error is None
    assert len(controller.pending_tokens) == 3
    assert len(controller.legal_token_coordinates()) == 37
    assert Coordinate(0, 0) in controller.legal_token_coordinates()


def test_controller_reports_turn_completion_and_friendly_errors() -> None:
    controller = GameController(build_state())

    assert controller.can_end_turn() is False
    assert controller.end_turn() == "the mandatory token draft action has not been taken"

    controller.draft_offer(0)
    controller.place_next_token(Coordinate(0, 0))
    controller.place_next_token(Coordinate(1, 0))
    controller.place_next_token(Coordinate(2, 0))

    assert controller.can_end_turn() is True
    assert controller.end_turn() is None
    assert controller.current_player_index == 1


def test_controller_enumerates_legal_animal_placements_after_board_setup() -> None:
    controller = GameController(build_state())
    controller.draft_offer(0)
    controller.place_next_token(Coordinate(0, 0))
    controller.take_animal_card(0)
    controller.place_next_token(Coordinate(1, 0))

    placements = controller.legal_animal_placements(card_index=0)

    assert placements
    assert any(
        placement.anchor == Coordinate(0, 0)
        and placement.rotation == 0
        and placement.target == Coordinate(0, 0)
        for placement in placements
    )


def test_board_layout_maps_center_and_supports_directional_navigation() -> None:
    state = build_state()
    board = state.players[0].board
    layout = build_board_layout(board)

    assert layout.position_for(Coordinate(0, 0)).row == 6
    assert layout.position_for(Coordinate(0, 0)).column == 18
    assert layout.move_left(board, Coordinate(0, 0)) == Coordinate(-1, 0)
    assert layout.move_right(board, Coordinate(0, 0)) == Coordinate(1, 0)
    assert layout.move_up(board, Coordinate(0, 0)) == Coordinate(0, -1)
    assert layout.move_down(board, Coordinate(0, 0)) == Coordinate(-1, 1)


def test_renderer_shows_cursor_highlight_and_summary() -> None:
    state = build_state()
    state = GameRules.draft_offer(state, 0)
    state = GameRules.place_next_token(state, Coordinate(0, 0))

    layout = build_board_layout(state.players[0].board)
    board_text = render_board(
        state,
        layout,
        player_index=0,
        cursor=Coordinate(0, 0),
        highlights=frozenset({Coordinate(1, 0)}),
        preview_target=Coordinate(0, 0),
    )
    summary_text = render_game_summary(state)

    assert "<Mt >" in board_text
    assert "{.  }" in board_text
    assert "Player 1 turn" in summary_text
    assert "Pending tokens: field, wood" in summary_text


def test_parse_coordinate_requires_q_r_format() -> None:
    coordinate = parse_coordinate("1, -2")

    assert coordinate == Coordinate(1, -2)


def test_terminal_shell_command_flow_and_screen_render() -> None:
    controller = GameController(build_state())

    assert handle_command(controller, "draft 0") == "offer drafted"
    assert handle_command(controller, "place 0,0") == "token placed"

    screen_text = render_screen(controller)

    assert "Offers:" in screen_text
    assert "Animal Row:" in screen_text
    assert "Active Cards:" in screen_text
    assert "Mt" in screen_text