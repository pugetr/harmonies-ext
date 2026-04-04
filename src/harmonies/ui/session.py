from __future__ import annotations

from dataclasses import dataclass, field

from harmonies.game import GameRules
from harmonies.model import Coordinate
from harmonies.ui.controller import AnimalPlacementOption, GameController
from harmonies.ui.layout import BoardLayout, build_board_layout
from harmonies.ui.render import (
    ACTIVE_DRAFT_BACKGROUND,
    DRAFTED_OFFER_BACKGROUND,
    PREVIEW_TARGET_BACKGROUND,
    QUEUED_DRAFT_BACKGROUND,
    SELECTED_LINE_STYLE,
    render_board,
    render_board_markup,
    render_game_summary,
    terrain_markup_label,
)


INITIAL_MESSAGE = (
    "Draft an offer to begin. Move with arrows or hjkl, press d to draft, "
    "p or Enter to place, t to take an animal card, and r to rotate cube previews."
)


@dataclass
class GameSession:
    controller: GameController
    message: str = INITIAL_MESSAGE
    selected_offer_index: int = 0
    selected_animal_row_index: int = 0
    selected_card_index: int = 0
    selected_rotation: int = 0
    layout: BoardLayout = field(init=False)
    cursor: Coordinate = field(init=False)
    preferred_vertical_column: int = field(init=False)

    def __post_init__(self) -> None:
        self.layout = build_board_layout(self.current_player.board)
        self.cursor = self._default_cursor()
        self._normalize_selection_state()

    @property
    def state(self):
        return self.controller.state

    @property
    def current_player(self):
        return self.controller.current_player

    @property
    def current_player_index(self) -> int:
        return self.controller.current_player_index

    @property
    def phase(self) -> str:
        if self.state.game_over:
            return "game_over"
        if self.state.turn.drafted_offer_index is None:
            return "draft"
        if self.state.turn.pending_tokens:
            return "place_tokens"
        return "actions"

    def move_cursor(self, direction: str) -> None:
        board = self.current_player.board
        if direction == "left":
            self.cursor = self.layout.move_left(board, self.cursor)
            self.preferred_vertical_column = self.layout.position_for(self.cursor).column
        elif direction == "right":
            self.cursor = self.layout.move_right(board, self.cursor)
            self.preferred_vertical_column = self.layout.position_for(self.cursor).column
        elif direction == "up":
            self._move_cursor_vertical(direction)
        elif direction == "down":
            self._move_cursor_vertical(direction)

    def cycle_offer(self) -> None:
        indexes = self.available_offer_indexes()
        if not indexes:
            self.message = "No offers remain."
            return
        self.selected_offer_index = self._next_index(self.selected_offer_index, indexes)
        self.message = f"Selected offer {self.selected_offer_index}."

    def cycle_animal_row(self) -> None:
        indexes = tuple(range(len(self.state.animal_row)))
        if not indexes:
            self.message = "The animal row is empty."
            return
        self.selected_animal_row_index = self._next_index(self.selected_animal_row_index, indexes)
        card = self.state.animal_row[self.selected_animal_row_index]
        self.message = f"Selected animal row card {self.selected_animal_row_index}: {card.name}."

    def cycle_active_card(self) -> None:
        indexes = tuple(range(len(self.current_player.active_cards)))
        if not indexes:
            self.message = "You do not have any active animal cards."
            return
        self.selected_card_index = self._next_index(self.selected_card_index, indexes)
        card = self.current_player.active_cards[self.selected_card_index]
        self.message = f"Selected active card {self.selected_card_index}: {card.definition.name}."

    def rotate_preview(self) -> None:
        if not self.current_player.active_cards:
            self.message = "You do not have any active animal cards to rotate."
            return
        self.selected_rotation = (self.selected_rotation + 1) % 6
        preview = self.current_preview()
        if preview is None:
            self.message = f"Rotation {self.selected_rotation}: no legal cube placement at the cursor."
            return
        self.message = (
            f"Rotation {self.selected_rotation}: previewing cube target "
            f"{format_coordinate(preview.target)}."
        )

    def draft_selected_offer(self) -> None:
        if self.state.game_over:
            self.message = "The game is over."
            return
        error = self.controller.draft_offer(self.selected_offer_index)
        if error:
            self.message = error
            return
        drafted = ", ".join(color.value for color in self.state.turn.pending_tokens)
        self.message = f"Drafted offer {self.selected_offer_index}: {drafted}."
        self._normalize_selection_state()

    def take_selected_animal_card(self) -> None:
        if self.state.game_over:
            self.message = "The game is over."
            return
        if not self.state.animal_row:
            self.message = "There are no animal cards left in the row."
            return
        card_name = self.state.animal_row[self.selected_animal_row_index].name
        error = self.controller.take_animal_card(self.selected_animal_row_index)
        if error:
            self.message = error
            return
        self.message = f"Took animal card {card_name}."
        self._normalize_selection_state()

    def place_at_cursor(self) -> None:
        if self.state.game_over:
            self.message = "The game is over."
            return
        if self.state.turn.pending_tokens:
            color = self.state.turn.pending_tokens[0]
            error = self.controller.place_next_token(self.cursor)
            if error:
                self.message = error
                return
            self.message = f"Placed {color.value} at {format_coordinate(self.cursor)}."
            self._normalize_selection_state()
            return

        preview = self.current_preview()
        if preview is None:
            self.message = "No legal animal cube placement matches the cursor and selected rotation."
            return
        card_name = self.current_player.active_cards[preview.card_index].definition.name
        error = self.controller.place_animal_cube(preview.card_index, preview.anchor, preview.rotation)
        if error:
            self.message = error
            return
        self.message = (
            f"Placed a cube for {card_name} at {format_coordinate(preview.target)} "
            f"from anchor {format_coordinate(preview.anchor)}."
        )
        self._normalize_selection_state()

    def end_turn(self) -> None:
        if self.state.game_over:
            self.message = self.render_winner_message()
            return
        next_player = (self.current_player_index % len(self.state.players)) + 1
        error = self.controller.end_turn()
        if error:
            self.message = error
            return
        self.selected_rotation = 0
        self._normalize_selection_state()
        if self.state.game_over:
            self.message = self.render_winner_message()
            return
        self.message = f"Turn ended. Player {next_player} is now active."

    def available_offer_indexes(self) -> tuple[int, ...]:
        return tuple(index for index, offer in enumerate(self.state.offers) if offer)

    def current_preview(self) -> AnimalPlacementOption | None:
        if not self.current_player.active_cards:
            return None
        if self.selected_card_index >= len(self.current_player.active_cards):
            return None
        for placement in self.controller.legal_animal_placements(card_index=self.selected_card_index):
            if placement.anchor == self.cursor and placement.rotation == self.selected_rotation:
                return placement
        return None

    def board_highlights(self) -> frozenset[Coordinate]:
        if self.state.turn.pending_tokens:
            return frozenset(self.controller.legal_token_coordinates())
        if not self.current_player.active_cards:
            return frozenset()
        return frozenset(
            placement.anchor
            for placement in self.controller.legal_animal_placements(card_index=self.selected_card_index)
            if placement.rotation == self.selected_rotation
        )

    def render_board_panel(self) -> str:
        return render_board(
            self.state,
            self.layout,
            player_index=self.current_player_index,
            cursor=self.cursor,
            highlights=self.board_highlights(),
            preview_target=self.preview_target(),
        )

    def render_board_panel_markup(self) -> str:
        return render_board_markup(
            self.state,
            self.layout,
            player_index=self.current_player_index,
            cursor=self.cursor,
            highlights=self.board_highlights(),
            preview_target=self.preview_target(),
        )

    def render_summary_panel(self) -> str:
        lines = ["Summary", "", *render_game_summary(self.state).splitlines()]
        lines.append(f"Bag tokens left: {len(self.state.bag)}")
        lines.append(f"Animal deck left: {len(self.state.animal_deck)}")
        lines.append(f"Phase: {self.phase_label()}")
        if self.state.final_round_target_turns is not None:
            lines.append(f"Final round target turns: {self.state.final_round_target_turns}")
        lines.append("")
        lines.append("Scores")
        for player_index in range(len(self.state.players)):
            breakdown = GameRules.score_player(self.state, player_index)
            marker = ">" if player_index == self.current_player_index else " "
            lines.append(f"{marker} P{player_index + 1}: {breakdown.total} points")
            if self.state.game_over:
                lines.append(
                    "    "
                    f"trees {breakdown.trees}, mountains {breakdown.mountains}, "
                    f"fields {breakdown.fields}, water {breakdown.water}, "
                    f"buildings {breakdown.buildings}, animals {breakdown.animals}"
                )
        return "\n".join(lines)

    def render_summary_panel_markup(self) -> str:
        lines = ["Summary", "", f"Player {self.state.current_player + 1} turn"]
        lines.append(f"Pending tokens: {self.render_pending_tokens_markup()}")
        lines.append(f"Animal card taken: {'yes' if self.state.turn.animal_card_taken else 'no'}")
        lines.append(f"Offers available: {sum(1 for offer in self.state.offers if offer)}")
        lines.append(f"Animal cards in row: {len(self.state.animal_row)}")
        lines.append(f"Bag tokens left: {len(self.state.bag)}")
        lines.append(f"Animal deck left: {len(self.state.animal_deck)}")
        lines.append(f"Phase: {self.phase_label()}")
        if self.state.final_round_target_turns is not None:
            lines.append(f"Final round target turns: {self.state.final_round_target_turns}")
        lines.append("")
        lines.append("Scores")
        for player_index in range(len(self.state.players)):
            breakdown = GameRules.score_player(self.state, player_index)
            prefix = ">" if player_index == self.current_player_index else " "
            lines.append(f"{prefix} P{player_index + 1}: {breakdown.total} points")
            if self.state.game_over:
                lines.append(
                    "    "
                    f"trees {breakdown.trees}, mountains {breakdown.mountains}, "
                    f"fields {breakdown.fields}, water {breakdown.water}, "
                    f"buildings {breakdown.buildings}, animals {breakdown.animals}"
                )
        return "\n".join(lines)

    def render_offers_panel(self) -> str:
        lines = ["Offers", ""]
        available = set(self.available_offer_indexes())
        for index, offer in enumerate(self.state.offers):
            marker = ">" if index == self.selected_offer_index else " "
            label = ", ".join(color.value for color in offer) if offer else "taken"
            status = []
            if index == self.state.turn.drafted_offer_index:
                status.append("drafted")
            elif index in available and self.phase == "draft":
                status.append("press d")
            suffix = f" [{', '.join(status)}]" if status else ""
            lines.append(f"{marker} {index}: {label}{suffix}")
        return "\n".join(lines)

    def render_offers_panel_markup(self) -> str:
        lines = ["Offers", ""]
        available = set(self.available_offer_indexes())
        for index, offer in enumerate(self.state.offers):
            line_style = []
            marker = ">" if index == self.selected_offer_index else " "
            if index == self.selected_offer_index:
                line_style.append(SELECTED_LINE_STYLE)
            if index == self.state.turn.drafted_offer_index:
                line_style.append(f"on {DRAFTED_OFFER_BACKGROUND}")
            prefix = f"[{ ' '.join(line_style) }]{marker} {index}:[/]" if line_style else f"{marker} {index}:"

            if offer:
                background = DRAFTED_OFFER_BACKGROUND if index == self.state.turn.drafted_offer_index else None
                label = ", ".join(terrain_markup_label(color, background=background) for color in offer)
            else:
                label = "[dim]taken[/]"

            status = []
            if index == self.state.turn.drafted_offer_index:
                status.append("drafted")
            elif index in available and self.phase == "draft":
                status.append("press d")
            suffix = f" [dim]({', '.join(status)})[/dim]" if status else ""
            lines.append(f"{prefix} {label}{suffix}")
        return "\n".join(lines)

    def render_animal_row_panel(self) -> str:
        lines = ["Animal Row", ""]
        if not self.state.animal_row:
            lines.append("  none")
            return "\n".join(lines)

        for index, card in enumerate(self.state.animal_row):
            marker = ">" if index == self.selected_animal_row_index else " "
            suffix = " [press t]" if index == self.selected_animal_row_index else ""
            lines.append(f"{marker} {index}: {card.name} ({card.card_id}){suffix}")
        return "\n".join(lines)

    def render_active_cards_panel(self) -> str:
        lines = ["Active Cards", "", f"Rotation: {self.selected_rotation}"]
        if not self.current_player.active_cards:
            lines.append("  none")
            return "\n".join(lines)

        for index, card in enumerate(self.current_player.active_cards):
            marker = ">" if index == self.selected_card_index else " "
            preview = " [preview]" if index == self.selected_card_index else ""
            lines.append(
                f"{marker} {index}: {card.definition.name} "
                f"{card.cubes_placed}/{card.definition.cube_count}{preview}"
            )
        return "\n".join(lines)

    def render_cursor_panel(self) -> str:
        cell = self.current_player.board.cell(self.cursor)
        preview = self.current_preview()
        lines = ["Cursor", "", f"Coordinate: {format_coordinate(self.cursor)}"]
        lines.append(f"Height: {cell.height}")
        lines.append(f"Top token: {cell.top_color.value if cell.top_color else 'empty'}")
        lines.append(
            "Stack: " + (", ".join(token.value for token in cell.tokens) if cell.tokens else "empty")
        )
        lines.append(f"Cube marker: {cell.cube_marker or 'none'}")
        lines.append("")
        if preview is None:
            lines.append("Preview target: none")
        else:
            lines.append(f"Preview target: {format_coordinate(preview.target)}")
            lines.append(f"Preview card: {self.current_player.active_cards[preview.card_index].definition.name}")
        return "\n".join(lines)

    def render_message_panel(self) -> str:
        return "Message\n\n" + self.message

    def render_controls_panel(self) -> str:
        return "\n".join(
            [
                "Controls",
                "",
                "Move cursor: arrows or hjkl",
                "Cycle offer: o",
                "Cycle animal row: n",
                "Cycle active card: c",
                "Rotate preview: r",
                "Draft offer: d",
                "Take animal card: t",
                "Place token or cube: Enter, Space, p",
                "End turn: e",
                "Quit: q",
            ]
        )

    def render_screen(self) -> str:
        sections = [
            self.render_summary_panel(),
            self.render_offers_panel(),
            self.render_animal_row_panel(),
            self.render_active_cards_panel(),
            self.render_cursor_panel(),
            "Board\n\n" + self.render_board_panel(),
            self.render_message_panel(),
        ]
        return "\n\n".join(sections)

    def render_pending_tokens_markup(self) -> str:
        if not self.state.turn.pending_tokens:
            return "[dim]none[/]"

        pieces = []
        for index, color in enumerate(self.state.turn.pending_tokens):
            background = ACTIVE_DRAFT_BACKGROUND if index == 0 else QUEUED_DRAFT_BACKGROUND
            pieces.append(terrain_markup_label(color, background=background))
        return "  ".join(pieces)

    def preview_target(self) -> Coordinate | None:
        preview = self.current_preview()
        return preview.target if preview else None

    def phase_label(self) -> str:
        if self.phase == "draft":
            return "Draft an offer"
        if self.phase == "place_tokens":
            return "Place drafted terrain"
        if self.phase == "actions":
            return "Optional animal actions or end turn"
        return "Game over"

    def render_winner_message(self) -> str:
        scores = [GameRules.score_player(self.state, index).total for index in range(len(self.state.players))]
        best_score = max(scores)
        winners = [f"Player {index + 1}" for index, score in enumerate(scores) if score == best_score]
        if len(winners) == 1:
            return f"Game over. {winners[0]} wins with {best_score} points."
        return f"Game over. Tie at {best_score} points between {', '.join(winners)}."

    def _default_cursor(self) -> Coordinate:
        if Coordinate(0, 0) in self.current_player.board.spaces:
            return Coordinate(0, 0)
        return min(self.current_player.board.spaces)

    def _normalize_selection_state(self) -> None:
        self.layout = build_board_layout(self.current_player.board)
        if self.cursor not in self.current_player.board.spaces:
            self.cursor = self._default_cursor()
        self.preferred_vertical_column = self.layout.position_for(self.cursor).column
        self.selected_offer_index = self._normalize_index(
            self.selected_offer_index,
            self.available_offer_indexes(),
        )
        self.selected_animal_row_index = self._normalize_index(
            self.selected_animal_row_index,
            tuple(range(len(self.state.animal_row))),
        )
        self.selected_card_index = self._normalize_index(
            self.selected_card_index,
            tuple(range(len(self.current_player.active_cards))),
        )

    @staticmethod
    def _next_index(current: int, indexes: tuple[int, ...]) -> int:
        position = indexes.index(current) if current in indexes else -1
        return indexes[(position + 1) % len(indexes)]

    @staticmethod
    def _normalize_index(current: int, indexes: tuple[int, ...]) -> int:
        if not indexes:
            return 0
        if current in indexes:
            return current
        return indexes[0]

    def _move_cursor_vertical(self, direction: str) -> None:
        board = self.current_player.board
        source = self.layout.position_for(self.cursor)
        candidates = []

        for neighbor in self.cursor.neighbors():
            if neighbor not in board.spaces:
                continue
            target = self.layout.position_for(neighbor)
            if direction == "up" and target.row >= source.row:
                continue
            if direction == "down" and target.row <= source.row:
                continue
            candidates.append(
                (
                    abs(target.column - self.preferred_vertical_column),
                    abs(target.column - source.column),
                    target.column,
                    neighbor,
                )
            )

        if not candidates:
            return

        self.cursor = min(candidates)[3]


def format_coordinate(coordinate: Coordinate) -> str:
    return f"{coordinate.q},{coordinate.r}"