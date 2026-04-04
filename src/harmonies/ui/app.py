from __future__ import annotations

import random

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Static

from harmonies.cards import load_base_animal_deck
from harmonies.game import GameRules, build_bag
from harmonies.model import BoardSide
from harmonies.ui.controller import GameController
from harmonies.ui.session import GameSession


def build_default_controller() -> GameController:
    state = GameRules.create_game(
        player_count=2,
        board_side=BoardSide.A,
        bag=build_bag(rng=random.Random()),
        animal_deck=load_base_animal_deck(),
    )
    return GameController(state)


def render_screen(controller: GameController) -> str:
    return GameSession(controller).render_screen()


class HarmoniesTerminalApp(App[None]):
    TITLE = "Harmonies"
    SUB_TITLE = "Persistent full-screen terminal play"
    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        layout: horizontal;
        height: 1fr;
    }

    #board-pane {
        width: 1fr;
        border: round $accent;
        padding: 1 2;
        margin: 0 1 0 0;
    }

    #sidebar {
        width: 42;
        border: round $surface;
        padding: 0 1;
    }

    .panel {
        border: round $panel;
        padding: 1 2;
        margin: 0 0 1 0;
    }
    """
    BINDINGS = [
        Binding("left,h", "move_left", "Left", show=False),
        Binding("right,l", "move_right", "Right", show=False),
        Binding("up,k", "move_up", "Up", show=False),
        Binding("down,j", "move_down", "Down", show=False),
        Binding("o", "cycle_offer", "Offer"),
        Binding("n", "cycle_animal", "Animal"),
        Binding("c", "cycle_card", "Card"),
        Binding("r", "rotate", "Rotate"),
        Binding("d", "draft", "Draft"),
        Binding("t", "take_card", "Take"),
        Binding("enter,space,p", "place", "Place"),
        Binding("e", "end_turn", "End"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, controller: GameController | None = None) -> None:
        super().__init__()
        self.session = GameSession(controller or build_default_controller())

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield Static(id="board-pane")
            with VerticalScroll(id="sidebar"):
                yield Static(id="summary-pane", classes="panel")
                yield Static(id="offers-pane", classes="panel")
                yield Static(id="animal-pane", classes="panel")
                yield Static(id="cards-pane", classes="panel")
                yield Static(id="cursor-pane", classes="panel")
                yield Static(id="message-pane", classes="panel")
                yield Static(id="controls-pane", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_view()

    def refresh_view(self) -> None:
        self.query_one("#board-pane", Static).update(Text.from_markup(self.session.render_board_panel_markup()))
        self.query_one("#summary-pane", Static).update(Text.from_markup(self.session.render_summary_panel_markup()))
        self.query_one("#offers-pane", Static).update(Text.from_markup(self.session.render_offers_panel_markup()))
        self.query_one("#animal-pane", Static).update(Text(self.session.render_animal_row_panel()))
        self.query_one("#cards-pane", Static).update(Text(self.session.render_active_cards_panel()))
        self.query_one("#cursor-pane", Static).update(Text(self.session.render_cursor_panel()))
        self.query_one("#message-pane", Static).update(Text(self.session.render_message_panel()))
        self.query_one("#controls-pane", Static).update(Text(self.session.render_controls_panel()))

    def action_move_left(self) -> None:
        self.session.move_cursor("left")
        self.refresh_view()

    def action_move_right(self) -> None:
        self.session.move_cursor("right")
        self.refresh_view()

    def action_move_up(self) -> None:
        self.session.move_cursor("up")
        self.refresh_view()

    def action_move_down(self) -> None:
        self.session.move_cursor("down")
        self.refresh_view()

    def action_cycle_offer(self) -> None:
        self.session.cycle_offer()
        self.refresh_view()

    def action_cycle_animal(self) -> None:
        self.session.cycle_animal_row()
        self.refresh_view()

    def action_cycle_card(self) -> None:
        self.session.cycle_active_card()
        self.refresh_view()

    def action_rotate(self) -> None:
        self.session.rotate_preview()
        self.refresh_view()

    def action_draft(self) -> None:
        self.session.draft_selected_offer()
        self.refresh_view()

    def action_take_card(self) -> None:
        self.session.take_selected_animal_card()
        self.refresh_view()

    def action_place(self) -> None:
        self.session.place_at_cursor()
        self.refresh_view()

    def action_end_turn(self) -> None:
        self.session.end_turn()
        self.refresh_view()


def main() -> int:
    HarmoniesTerminalApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())