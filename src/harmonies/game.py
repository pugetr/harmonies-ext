from __future__ import annotations

from dataclasses import dataclass, replace
import random
from typing import Optional

from harmonies.board import create_player_board
from harmonies.cards import AnimalCardDefinition, AnimalCardState, resolve_habitat_target
from harmonies.model import BoardSide, Coordinate, TerrainColor
from harmonies.scoring import ScoreBreakdown, score_breakdown


DEFAULT_BAG_COUNTS: dict[TerrainColor, int] = {
    TerrainColor.WATER: 23,
    TerrainColor.MOUNTAIN: 23,
    TerrainColor.WOOD: 21,
    TerrainColor.LEAF: 19,
    TerrainColor.FIELD: 19,
    TerrainColor.BUILDING: 15,
}


@dataclass(frozen=True)
class TurnState:
    drafted_offer_index: Optional[int] = None
    pending_tokens: tuple[TerrainColor, ...] = ()
    animal_card_taken: bool = False


@dataclass(frozen=True)
class PlayerState:
    board: PlayerBoard
    active_cards: tuple[AnimalCardState, ...] = ()
    completed_cards: tuple[AnimalCardState, ...] = ()
    placed_cube_total: int = 0

    def all_cards(self) -> tuple[AnimalCardState, ...]:
        return self.active_cards + self.completed_cards


@dataclass(frozen=True)
class GameState:
    players: tuple[PlayerState, ...]
    current_player: int
    bag: tuple[TerrainColor, ...]
    offers: tuple[tuple[TerrainColor, ...], ...]
    animal_row: tuple[AnimalCardDefinition, ...]
    animal_deck: tuple[AnimalCardDefinition, ...]
    turns_taken: tuple[int, ...]
    turn: TurnState = TurnState()
    final_round_target_turns: Optional[int] = None
    game_over: bool = False


class GameRules:
    @staticmethod
    def create_game(
        player_count: int,
        board_side: BoardSide,
        bag: tuple[TerrainColor, ...],
        animal_deck: tuple[AnimalCardDefinition, ...],
        start_player: int = 0,
    ) -> GameState:
        if player_count < 2 or player_count > 4:
            raise ValueError("base multiplayer Harmonies supports 2 to 4 players")
        if len(animal_deck) < 5:
            raise ValueError("at least 5 animal cards are required to start the game")

        remaining_bag = bag
        offers: list[tuple[TerrainColor, ...]] = []
        for _ in range(5):
            draw, remaining_bag = _draw(remaining_bag, 3)
            offers.append(draw)

        animal_row, animal_deck = animal_deck[:5], animal_deck[5:]
        players = tuple(
            PlayerState(board=create_player_board(board_side))
            for _ in range(player_count)
        )
        turns_taken = tuple(0 for _ in range(player_count))

        return GameState(
            players=players,
            current_player=start_player,
            bag=remaining_bag,
            offers=tuple(offers),
            animal_row=animal_row,
            animal_deck=animal_deck,
            turns_taken=turns_taken,
        )

    @staticmethod
    def draft_offer(state: GameState, offer_index: int) -> GameState:
        _assert_not_game_over(state)
        if state.turn.drafted_offer_index is not None:
            raise ValueError("you have already drafted an offer this turn")

        offer = state.offers[offer_index]
        if len(offer) != 3:
            raise ValueError("the chosen offer is not available")

        offers = _replace_index(state.offers, offer_index, ())
        turn = replace(state.turn, drafted_offer_index=offer_index, pending_tokens=offer)
        return replace(state, offers=offers, turn=turn)

    @staticmethod
    def place_next_token(state: GameState, coordinate: Coordinate) -> GameState:
        _assert_not_game_over(state)
        if not state.turn.pending_tokens:
            raise ValueError("there are no pending drafted tokens to place")

        color = state.turn.pending_tokens[0]
        player = state.players[state.current_player]
        updated_board = player.board.place_token(color, coordinate)
        updated_player = replace(player, board=updated_board)
        updated_players = _replace_index(state.players, state.current_player, updated_player)
        updated_turn = replace(state.turn, pending_tokens=state.turn.pending_tokens[1:])
        return replace(state, players=updated_players, turn=updated_turn)

    @staticmethod
    def take_animal_card(state: GameState, row_index: int) -> GameState:
        _assert_not_game_over(state)
        if state.turn.animal_card_taken:
            raise ValueError("you may take at most one animal card per turn")

        player = state.players[state.current_player]
        if len(player.active_cards) >= 4:
            raise ValueError("you may not hold more than 4 active animal cards")

        card = state.animal_row[row_index]
        active_cards = player.active_cards + (AnimalCardState(definition=card),)
        updated_player = replace(player, active_cards=active_cards)
        updated_players = _replace_index(state.players, state.current_player, updated_player)
        updated_row = _remove_index(state.animal_row, row_index)
        updated_turn = replace(state.turn, animal_card_taken=True)
        return replace(state, players=updated_players, animal_row=updated_row, turn=updated_turn)

    @staticmethod
    def place_animal_cube(
        state: GameState,
        card_index: int,
        anchor: Coordinate,
        rotation: int = 0,
    ) -> GameState:
        _assert_not_game_over(state)

        player = state.players[state.current_player]
        card_state = player.active_cards[card_index]
        target = resolve_habitat_target(player.board, card_state.definition.habitat, anchor, rotation)
        marker = f"{card_state.definition.card_id}:{card_state.cubes_placed + 1}"
        updated_board = player.board.place_cube(target, marker)
        updated_card = card_state.place_cube()

        active_cards = list(player.active_cards)
        completed_cards = list(player.completed_cards)
        if updated_card.complete:
            active_cards.pop(card_index)
            completed_cards.append(updated_card)
        else:
            active_cards[card_index] = updated_card

        updated_player = replace(
            player,
            board=updated_board,
            active_cards=tuple(active_cards),
            completed_cards=tuple(completed_cards),
            placed_cube_total=player.placed_cube_total + 1,
        )
        updated_players = _replace_index(state.players, state.current_player, updated_player)
        return replace(state, players=updated_players)

    @staticmethod
    def end_turn(state: GameState) -> GameState:
        _assert_not_game_over(state)
        if state.turn.drafted_offer_index is None:
            raise ValueError("the mandatory token draft action has not been taken")
        if state.turn.pending_tokens:
            raise ValueError("all drafted tokens must be placed before ending the turn")

        current = state.current_player
        turns_taken = list(state.turns_taken)
        turns_taken[current] += 1

        offers = state.offers
        bag = state.bag
        bag_triggered_end = False
        try:
            refill, bag = _draw(bag, 3)
            offers = _replace_index(offers, state.turn.drafted_offer_index, refill)
        except ValueError:
            bag_triggered_end = True

        animal_row = state.animal_row
        animal_deck = state.animal_deck
        while len(animal_row) < 5 and animal_deck:
            animal_row = animal_row + (animal_deck[0],)
            animal_deck = animal_deck[1:]

        board_triggered_end = state.players[current].board.empty_space_count() <= 2
        final_round_target_turns = state.final_round_target_turns
        if final_round_target_turns is None and (bag_triggered_end or board_triggered_end):
            final_round_target_turns = turns_taken[current]

        game_over = final_round_target_turns is not None and all(
            turn_count >= final_round_target_turns for turn_count in turns_taken
        )
        next_player = current if game_over else (current + 1) % len(state.players)

        return replace(
            state,
            current_player=next_player,
            bag=bag,
            offers=offers,
            animal_row=animal_row,
            animal_deck=animal_deck,
            turns_taken=tuple(turns_taken),
            turn=TurnState(),
            final_round_target_turns=final_round_target_turns,
            game_over=game_over,
        )

    @staticmethod
    def score_player(state: GameState, player_index: int) -> ScoreBreakdown:
        player = state.players[player_index]
        return score_breakdown(player.board, player.all_cards())


def build_bag(
    counts: Optional[dict[TerrainColor, int]] = None,
    *,
    rng: Optional[random.Random] = None,
) -> tuple[TerrainColor, ...]:
    contents = counts or DEFAULT_BAG_COUNTS
    bag: list[TerrainColor] = []
    for color, count in contents.items():
        bag.extend(color for _ in range(count))
    if rng is not None:
        rng.shuffle(bag)
    return tuple(bag)


def _assert_not_game_over(state: GameState) -> None:
    if state.game_over:
        raise ValueError("the game is already over")


def _draw(values: tuple, count: int) -> tuple[tuple, tuple]:
    if len(values) < count:
        raise ValueError("not enough items to draw")
    return values[:count], values[count:]


def _replace_index(values: tuple, index: int, replacement):
    mutable = list(values)
    mutable[index] = replacement
    return tuple(mutable)


def _remove_index(values: tuple, index: int):
    mutable = list(values)
    mutable.pop(index)
    return tuple(mutable)
