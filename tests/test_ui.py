import asyncio

from harmonies.cards import AnimalCardDefinition, HabitatPattern, StackRequirement
from harmonies.game import GameRules
from harmonies.model import BoardSide, Coordinate, TerrainColor
from harmonies.ui import GameController, build_board_layout, render_board, render_game_summary
from harmonies.ui.app import HarmoniesTerminalApp, render_screen
from harmonies.ui.session import GameSession, format_coordinate
from harmonies.ui.render import render_board_markup


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


def test_markup_board_keeps_terrain_visible_under_cursor() -> None:
    state = build_state()
    state = GameRules.draft_offer(state, 0)
    state = GameRules.place_next_token(state, Coordinate(0, 0))

    layout = build_board_layout(state.players[0].board)
    board_markup = render_board_markup(
        state,
        layout,
        player_index=0,
        cursor=Coordinate(0, 0),
    )

    assert "Mt" in board_markup
    assert "underline" in board_markup


def test_session_places_tokens_and_reports_board_state() -> None:
    session = GameSession(GameController(build_state()))

    session.draft_selected_offer()

    assert session.phase == "place_tokens"
    assert Coordinate(0, 0) in session.board_highlights()

    session.place_at_cursor()

    assert format_coordinate(session.cursor) in session.message
    assert session.current_player.board.cell(Coordinate(0, 0)).top_color == TerrainColor.MOUNTAIN


def test_session_vertical_navigation_stays_in_two_columns() -> None:
    session = GameSession(GameController(build_state()))

    visited_columns = [session.layout.position_for(session.cursor).column]

    session.move_cursor("up")
    visited_columns.append(session.layout.position_for(session.cursor).column)
    session.move_cursor("up")
    visited_columns.append(session.layout.position_for(session.cursor).column)
    session.move_cursor("up")
    visited_columns.append(session.layout.position_for(session.cursor).column)

    assert len(set(visited_columns)) == 2
    assert session.cursor == Coordinate(1, -3)

    session.move_cursor("down")
    session.move_cursor("down")
    session.move_cursor("down")

    assert session.cursor == Coordinate(0, 0)


def test_session_previews_and_places_animal_cube() -> None:
    controller = GameController(build_state())
    controller.draft_offer(0)
    controller.place_next_token(Coordinate(0, 0))
    controller.take_animal_card(0)
    controller.place_next_token(Coordinate(1, 0))
    controller.place_next_token(Coordinate(2, 0))
    session = GameSession(controller)

    preview = session.current_preview()

    assert preview is not None
    assert preview.target == Coordinate(0, 0)

    session.place_at_cursor()

    assert session.current_player.board.cell(Coordinate(0, 0)).cube_marker == "card-0:1"
    assert "Placed a cube for Card-0" in session.message


def test_render_screen_includes_full_session_sections() -> None:
    controller = GameController(build_state())
    screen_text = render_screen(controller)

    assert "Summary" in screen_text
    assert "Offers" in screen_text
    assert "Active Cards" in screen_text
    assert "Board" in screen_text
    assert "Message" in screen_text


def test_summary_and_offers_markup_highlight_current_draft() -> None:
    session = GameSession(GameController(build_state()))
    session.draft_selected_offer()

    summary_markup = session.render_summary_panel_markup()
    offers_markup = session.render_offers_panel_markup()

    assert "#f6d365" in summary_markup
    assert "#4b3a16" in offers_markup


def test_textual_app_mounts_and_renders_panels() -> None:
    async def run_app() -> None:
        controller = GameController(build_state())
        controller.draft_offer(0)
        controller.place_next_token(Coordinate(0, 0))
        app = HarmoniesTerminalApp(controller)
        async with app.run_test():
            summary = app.query_one("#summary-pane").render().plain
            board = app.query_one("#board-pane").render().plain

            assert "Summary" in summary
            assert "Player 1 turn" in summary
            assert "Pending tokens: field  wood" in summary
            assert "Mt" in board

    asyncio.run(run_app())