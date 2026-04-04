from __future__ import annotations

from harmonies.cards import load_base_animal_deck
from harmonies.game import GameRules, build_bag
from harmonies.model import BoardSide, Coordinate
from harmonies.ui.controller import GameController
from harmonies.ui.layout import build_board_layout
from harmonies.ui.render import render_board, render_game_summary


HELP_TEXT = """Commands:
  help
  draft <offer_index>
  place <q>,<r>
  take <row_index>
  cube <card_index> <q>,<r> [rotation]
  end
  quit
"""


def build_default_controller() -> GameController:
    state = GameRules.create_game(
        player_count=2,
        board_side=BoardSide.A,
        bag=build_bag(),
        animal_deck=load_base_animal_deck(),
    )
    return GameController(state)


def parse_coordinate(raw_value: str) -> Coordinate:
    pieces = [part.strip() for part in raw_value.split(",")]
    if len(pieces) != 2:
        raise ValueError("coordinates must use q,r format")
    return Coordinate(q=int(pieces[0]), r=int(pieces[1]))


def render_screen(controller: GameController) -> str:
    layout = build_board_layout(controller.current_player.board)
    lines = [render_game_summary(controller.state)]
    lines.append("")
    lines.append(render_offers(controller))
    lines.append(render_animal_row(controller))
    lines.append(render_active_cards(controller))
    lines.append("")
    lines.append(render_board(controller.state, layout, player_index=controller.current_player_index))
    return "\n".join(lines)


def render_offers(controller: GameController) -> str:
    offers = []
    for index, offer in enumerate(controller.state.offers):
        terrain_names = ", ".join(color.value for color in offer) if offer else "taken"
        offers.append(f"  {index}: {terrain_names}")
    return "Offers:\n" + "\n".join(offers)


def render_animal_row(controller: GameController) -> str:
    cards = []
    for index, card in enumerate(controller.state.animal_row):
        cards.append(f"  {index}: {card.name} ({card.card_id})")
    if not cards:
        cards.append("  none")
    return "Animal Row:\n" + "\n".join(cards)


def render_active_cards(controller: GameController) -> str:
    cards = []
    for index, card in enumerate(controller.current_player.active_cards):
        cards.append(
            f"  {index}: {card.definition.name} cubes {card.cubes_placed}/{card.definition.cube_count}"
        )
    if not cards:
        cards.append("  none")
    return "Active Cards:\n" + "\n".join(cards)


def handle_command(controller: GameController, raw_command: str) -> str:
    command = raw_command.strip()
    if not command:
        return "enter a command"
    if command == "help":
        return HELP_TEXT.rstrip()
    if command == "quit":
        raise EOFError()

    parts = command.split()
    action = parts[0]

    try:
        if action == "draft" and len(parts) == 2:
            error = controller.draft_offer(int(parts[1]))
            return error or "offer drafted"
        if action == "place" and len(parts) == 2:
            error = controller.place_next_token(parse_coordinate(parts[1]))
            return error or "token placed"
        if action == "take" and len(parts) == 2:
            error = controller.take_animal_card(int(parts[1]))
            return error or "animal card taken"
        if action == "cube" and len(parts) in {3, 4}:
            rotation = int(parts[3]) if len(parts) == 4 else 0
            error = controller.place_animal_cube(
                int(parts[1]),
                parse_coordinate(parts[2]),
                rotation,
            )
            return error or "animal cube placed"
        if action == "end" and len(parts) == 1:
            error = controller.end_turn()
            return error or "turn ended"
    except ValueError as error:
        return str(error)

    return "unknown command; type 'help'"


def main() -> int:
    controller = build_default_controller()
    message = HELP_TEXT.rstrip()

    try:
        while True:
            print(render_screen(controller))
            print()
            print(message)
            raw_command = input("> ")
            message = handle_command(controller, raw_command)
            print()
    except EOFError:
        print("session ended")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())