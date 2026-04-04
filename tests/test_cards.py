from harmonies.cards import load_base_animal_deck
from harmonies.game import GameRules, build_bag
from harmonies.model import BoardSide, Coordinate, TerrainColor


def test_base_animal_deck_loads_all_simplified_cards() -> None:
    deck = load_base_animal_deck()

    assert len(deck) == 32
    assert deck[0].card_id == "base-card-01"
    assert deck[-1].card_id == "base-card-32"


def test_loaded_cards_preserve_scores_and_requirement_shapes() -> None:
    deck = load_base_animal_deck()

    first = deck[0]
    assert first.points_by_cubes_placed == (0, 16, 10, 5)
    assert first.habitat.target_offset == Coordinate(0, 0)
    assert first.habitat.requirements[Coordinate(0, 0)].top == TerrainColor.WATER
    assert first.habitat.requirements[Coordinate(-1, 1)].top == TerrainColor.LEAF

    building_card = deck[7]
    target_requirement = building_card.habitat.requirements[Coordinate(0, 0)]
    assert target_requirement.top == TerrainColor.BUILDING
    assert target_requirement.height == 2
    assert set(target_requirement.building_base_allowed) == {
        TerrainColor.MOUNTAIN,
        TerrainColor.WOOD,
        TerrainColor.BUILDING,
    }

    four_space_card = deck[31]
    assert set(four_space_card.habitat.requirements) == {
        Coordinate(0, 0),
        Coordinate(1, -1),
        Coordinate(1, 0),
        Coordinate(0, 1),
    }


def test_loaded_base_deck_can_start_a_game() -> None:
    state = GameRules.create_game(
        player_count=2,
        board_side=BoardSide.A,
        bag=build_bag(),
        animal_deck=load_base_animal_deck(),
    )

    assert len(state.animal_row) == 5
    assert len(state.animal_deck) == 27