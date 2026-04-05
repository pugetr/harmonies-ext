from random import Random

from harmonies.cards import AnimalCardDefinition, HabitatPattern, StackRequirement
from harmonies.game import GameRules, build_bag
from harmonies.model import BoardSide, Coordinate, TerrainColor


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


def test_turn_can_interleave_token_placement_card_take_and_cube_placement() -> None:
    state = build_state()
    state = GameRules.draft_offer(state, 0)
    state = GameRules.place_next_token(state, Coordinate(0, 0))
    state = GameRules.take_animal_card(state, 0)
    state = GameRules.place_next_token(state, Coordinate(1, 0))
    state = GameRules.place_animal_cube(state, 0, anchor=Coordinate(0, 0))
    state = GameRules.place_next_token(state, Coordinate(2, 0))

    assert state.players[0].placed_cube_total == 1
    assert state.players[0].active_cards[0].cubes_placed == 1


def test_cycle_pending_tokens_rotates_active_draft_order() -> None:
    state = build_state()
    state = GameRules.draft_offer(state, 0)

    assert state.turn.pending_tokens == (
        TerrainColor.MOUNTAIN,
        TerrainColor.FIELD,
        TerrainColor.WOOD,
    )

    state = GameRules.cycle_pending_tokens(state)

    assert state.turn.pending_tokens == (
        TerrainColor.FIELD,
        TerrainColor.WOOD,
        TerrainColor.MOUNTAIN,
    )

    state = GameRules.place_next_token(state, Coordinate(0, 0))

    assert state.players[0].board.cell(Coordinate(0, 0)).top_color == TerrainColor.FIELD


def test_completed_card_frees_active_card_slot() -> None:
    state = build_state()
    state = GameRules.draft_offer(state, 0)
    state = GameRules.place_next_token(state, Coordinate(0, 0))
    state = GameRules.take_animal_card(state, 0)
    state = GameRules.place_next_token(state, Coordinate(1, 0))
    state = GameRules.place_animal_cube(state, 0, anchor=Coordinate(0, 0))
    state = GameRules.place_next_token(state, Coordinate(2, 0))
    state = GameRules.end_turn(state)

    state = GameRules.draft_offer(state, 1)
    state = GameRules.place_next_token(state, Coordinate(-1, 0))
    state = GameRules.place_next_token(state, Coordinate(-1, 1))
    state = GameRules.place_next_token(state, Coordinate(-2, 1))
    state = GameRules.end_turn(state)

    state = GameRules.draft_offer(state, 2)
    state = GameRules.place_next_token(state, Coordinate(0, 1))
    state = GameRules.place_next_token(state, Coordinate(1, 1))
    state = GameRules.place_animal_cube(state, 0, anchor=Coordinate(0, 1))
    state = GameRules.place_next_token(state, Coordinate(2, 1))

    assert len(state.players[0].active_cards) == 0
    assert len(state.players[0].completed_cards) == 1


def test_endgame_triggers_final_round_when_bag_cannot_refill_offer() -> None:
    cards = tuple(simple_card(f"card-{index}") for index in range(5))
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
    )
    state = GameRules.create_game(
        player_count=2,
        board_side=BoardSide.A,
        bag=bag,
        animal_deck=cards,
    )

    state = GameRules.draft_offer(state, 0)
    state = GameRules.place_next_token(state, Coordinate(0, 0))
    state = GameRules.place_next_token(state, Coordinate(1, 0))
    state = GameRules.place_next_token(state, Coordinate(0, 1))
    state = GameRules.end_turn(state)

    assert state.final_round_target_turns == 1
    assert state.game_over is False

    state = GameRules.draft_offer(state, 1)
    state = GameRules.place_next_token(state, Coordinate(-1, 0))
    state = GameRules.place_next_token(state, Coordinate(-1, 1))
    state = GameRules.place_next_token(state, Coordinate(-2, 1))
    state = GameRules.end_turn(state)

    assert state.game_over is True


def test_build_bag_can_shuffle_with_supplied_rng() -> None:
    bag = build_bag(
        counts={
            TerrainColor.WATER: 2,
            TerrainColor.MOUNTAIN: 1,
            TerrainColor.WOOD: 1,
            TerrainColor.LEAF: 1,
            TerrainColor.FIELD: 1,
            TerrainColor.BUILDING: 1,
        },
        rng=Random(7),
    )

    assert bag == (
        TerrainColor.FIELD,
        TerrainColor.BUILDING,
        TerrainColor.LEAF,
        TerrainColor.WATER,
        TerrainColor.WOOD,
        TerrainColor.WATER,
        TerrainColor.MOUNTAIN,
    )
