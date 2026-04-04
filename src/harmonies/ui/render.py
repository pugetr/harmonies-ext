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


def render_game_summary(state: GameState) -> str:
    lines = [
        f"Player {state.current_player + 1} turn",
        f"Pending tokens: {', '.join(color.value for color in state.turn.pending_tokens) or 'none'}",
        f"Animal card taken: {'yes' if state.turn.animal_card_taken else 'no'}",
        f"Offers available: {sum(1 for offer in state.offers if offer)}",
        f"Animal cards in row: {len(state.animal_row)}",
    ]
    return "\n".join(lines)