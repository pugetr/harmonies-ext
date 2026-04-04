from __future__ import annotations

from harmonies.game import GameState
from harmonies.model import Coordinate, TerrainColor
from harmonies.ui.layout import BoardLayout


TERRAIN_SYMBOLS = {
    TerrainColor.WATER: "Wa",
    TerrainColor.MOUNTAIN: "Mt",
    TerrainColor.WOOD: "Wo",
    TerrainColor.LEAF: "Le",
    TerrainColor.FIELD: "Fi",
    TerrainColor.BUILDING: "Bu",
}

TERRAIN_COLORS = {
    TerrainColor.WATER: "#4fb0c6",
    TerrainColor.MOUNTAIN: "#d4d8dd",
    TerrainColor.WOOD: "#5d9c59",
    TerrainColor.LEAF: "#8bcf5d",
    TerrainColor.FIELD: "#d9b44a",
    TerrainColor.BUILDING: "#c67ad9",
}

LEGAL_HIGHLIGHT_BACKGROUND = "#203d29"
PREVIEW_TARGET_BACKGROUND = "#5d3c1b"
ACTIVE_DRAFT_BACKGROUND = "#f6d365"
QUEUED_DRAFT_BACKGROUND = "#ead39c"
DRAFTED_OFFER_BACKGROUND = "#4b3a16"
SELECTED_LINE_STYLE = "bold underline"


def terrain_markup_label(color: TerrainColor, background: str | None = None) -> str:
    style = terrain_markup_style(color, background=background)
    return f"[{style}]{color.value}[/]"


def terrain_markup_style(color: TerrainColor, background: str | None = None) -> str:
    style = f"bold {TERRAIN_COLORS[color]}"
    if background is not None:
        style = f"{style} on {background}"
    return style


def render_board(
    state: GameState,
    layout: BoardLayout,
    player_index: int,
    cursor: Coordinate | None = None,
    highlights: frozenset[Coordinate] = frozenset(),
    preview_target: Coordinate | None = None,
) -> str:
    board = state.players[player_index].board
    positions = tuple(layout.positions.values())
    height = max(position.row for position in positions) + 1
    width = max(position.column for position in positions) + 6
    canvas = [list(" " * width) for _ in range(height)]

    for coordinate in sorted(board.spaces, key=lambda item: (item.r, item.q)):
        position = layout.position_for(coordinate)
        cell = board.cell(coordinate)
        token_text = "."
        if cell.tokens:
            token_text = TERRAIN_SYMBOLS[cell.top_color]
            if len(cell.tokens) > 1:
                token_text = f"{token_text}{len(cell.tokens)}"

        left_marker = "[" if coordinate == cursor else " "
        right_marker = "]" if coordinate == cursor else " "
        if coordinate in highlights:
            left_marker = "{" if coordinate != cursor else "<"
            right_marker = "}" if coordinate != cursor else ">"
        if coordinate == preview_target:
            left_marker = "(" if coordinate != cursor else "<"
            right_marker = ")" if coordinate != cursor else ">"

        text = f"{left_marker}{token_text:<3}{right_marker}"
        if cell.cube_marker:
            text = f"{text[:-1]}*"

        for offset, character in enumerate(text):
            canvas[position.row][position.column + offset] = character

    return "\n".join("".join(row).rstrip() for row in canvas).rstrip()


def render_board_markup(
    state: GameState,
    layout: BoardLayout,
    player_index: int,
    cursor: Coordinate | None = None,
    highlights: frozenset[Coordinate] = frozenset(),
    preview_target: Coordinate | None = None,
) -> str:
    board = state.players[player_index].board
    rows: dict[int, list[tuple[int, str]]] = {}

    for coordinate in sorted(board.spaces, key=lambda item: (item.r, item.q)):
        position = layout.position_for(coordinate)
        rows.setdefault(position.row, []).append(
            (
                position.column,
                _render_markup_cell(
                    board.cell(coordinate),
                    coordinate == cursor,
                    coordinate in highlights,
                    coordinate == preview_target,
                ),
            )
        )

    height = max(position.row for position in layout.positions.values()) + 1
    lines: list[str] = []
    for row_index in range(height):
        entries = sorted(rows.get(row_index, ()))
        if not entries:
            lines.append("")
            continue

        cursor_column = 0
        line_parts: list[str] = []
        for column, cell_markup in entries:
            line_parts.append(" " * max(0, column - cursor_column))
            line_parts.append(cell_markup)
            cursor_column = column + 5
        lines.append("".join(line_parts))

    return "\n".join(lines).rstrip()


def _render_markup_cell(cell, is_cursor: bool, is_highlight: bool, is_preview_target: bool) -> str:
    token_text = "."
    style_parts = []
    if cell.tokens:
        token_text = TERRAIN_SYMBOLS[cell.top_color]
        if len(cell.tokens) > 1:
            token_text = f"{token_text}{len(cell.tokens)}"
        style_parts.append(terrain_markup_style(cell.top_color))
    else:
        style_parts.append("dim")

    if is_highlight:
        style_parts.append(f"on {LEGAL_HIGHLIGHT_BACKGROUND}")
    if is_preview_target:
        style_parts.append(f"on {PREVIEW_TARGET_BACKGROUND}")
    if is_cursor:
        style_parts.append("underline")
        style_parts.append("bold")

    cube_marker = "*" if cell.cube_marker else " "
    return f"[{' '.join(style_parts)}]{token_text:<4}{cube_marker}[/]"


def render_game_summary(state: GameState) -> str:
    lines = [
        f"Player {state.current_player + 1} turn",
        f"Pending tokens: {', '.join(color.value for color in state.turn.pending_tokens) or 'none'}",
        f"Animal card taken: {'yes' if state.turn.animal_card_taken else 'no'}",
        f"Offers available: {sum(1 for offer in state.offers if offer)}",
        f"Animal cards in row: {len(state.animal_row)}",
    ]
    return "\n".join(lines)