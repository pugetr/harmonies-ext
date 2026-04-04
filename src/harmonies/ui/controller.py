from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from harmonies.cards import resolve_habitat_target
from harmonies.game import GameRules, GameState
from harmonies.model import Coordinate


@dataclass(frozen=True)
class AnimalPlacementOption:
    card_index: int
    anchor: Coordinate
    rotation: int
    target: Coordinate


class GameController:
    def __init__(self, state: GameState):
        self.state = state

    @property
    def current_player_index(self) -> int:
        return self.state.current_player

    @property
    def current_player(self):
        return self.state.players[self.state.current_player]

    @property
    def pending_tokens(self) -> tuple:
        return self.state.turn.pending_tokens

    def available_offers(self) -> tuple[tuple[int, tuple], ...]:
        offers = []
        for index, offer in enumerate(self.state.offers):
            if offer:
                offers.append((index, offer))
        return tuple(offers)

    def can_take_animal_card(self) -> bool:
        return (
            not self.state.turn.animal_card_taken
            and len(self.current_player.active_cards) < 4
            and bool(self.state.animal_row)
        )

    def can_end_turn(self) -> bool:
        return self.state.turn.drafted_offer_index is not None and not self.state.turn.pending_tokens

    def legal_token_coordinates(self) -> tuple[Coordinate, ...]:
        if not self.state.turn.pending_tokens:
            return ()

        color = self.state.turn.pending_tokens[0]
        legal_coordinates = []
        for coordinate in sorted(self.current_player.board.spaces):
            try:
                self.current_player.board.place_token(color, coordinate)
            except ValueError:
                continue
            legal_coordinates.append(coordinate)
        return tuple(legal_coordinates)

    def legal_animal_placements(
        self,
        card_index: Optional[int] = None,
    ) -> tuple[AnimalPlacementOption, ...]:
        card_indexes = range(len(self.current_player.active_cards))
        if card_index is not None:
            card_indexes = (card_index,)

        placements = []
        for active_card_index in card_indexes:
            card_state = self.current_player.active_cards[active_card_index]
            for anchor in sorted(self.current_player.board.spaces):
                for rotation in range(6):
                    try:
                        target = resolve_habitat_target(
                            self.current_player.board,
                            card_state.definition.habitat,
                            anchor,
                            rotation,
                        )
                    except ValueError:
                        continue
                    placements.append(
                        AnimalPlacementOption(
                            card_index=active_card_index,
                            anchor=anchor,
                            rotation=rotation,
                            target=target,
                        )
                    )
        return tuple(placements)

    def draft_offer(self, offer_index: int) -> Optional[str]:
        return self._apply(GameRules.draft_offer, offer_index)

    def place_next_token(self, coordinate: Coordinate) -> Optional[str]:
        return self._apply(GameRules.place_next_token, coordinate)

    def take_animal_card(self, row_index: int) -> Optional[str]:
        return self._apply(GameRules.take_animal_card, row_index)

    def place_animal_cube(self, card_index: int, anchor: Coordinate, rotation: int = 0) -> Optional[str]:
        return self._apply(GameRules.place_animal_cube, card_index, anchor, rotation)

    def end_turn(self) -> Optional[str]:
        return self._apply(GameRules.end_turn)

    def _apply(self, action, *args) -> Optional[str]:
        try:
            self.state = action(self.state, *args)
        except ValueError as error:
            return str(error)
        return None