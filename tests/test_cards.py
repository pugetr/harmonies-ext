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
    assert first.points_by_cubes_placed == (0, 15, 9, 4)
    assert first.habitat.target_offset == Coordinate(0, 0)
    assert first.habitat.requirements[Coordinate(0, 0)].top == TerrainColor.WATER
    assert first.habitat.requirements[Coordinate(-1, 1)].top == TerrainColor.WATER
    assert first.habitat.requirements[Coordinate(-2, 2)].top == TerrainColor.LEAF
    assert first.habitat.requirements[Coordinate(-2, 2)].height == 3

    building_card = deck[7]
    target_requirement = building_card.habitat.requirements[Coordinate(0, 0)]
    assert target_requirement.top == TerrainColor.BUILDING
    assert target_requirement.height == 2
    assert set(target_requirement.building_base_allowed) == {
        TerrainColor.MOUNTAIN,
        TerrainColor.WOOD,
        TerrainColor.BUILDING,
    }

    four_space_card = deck[12]
    assert set(four_space_card.habitat.requirements) == {
        Coordinate(0, 0),
        Coordinate(1, -1),
        Coordinate(1, 0),
        Coordinate(0, 1),
    }


def test_loaded_cards_match_score_ladders_from_named_scans() -> None:
    deck = load_base_animal_deck()

    assert {card.card_id: card.points_by_cubes_placed[1:] for card in deck} == {
        "base-card-01": (15, 9, 4),
        "base-card-02": (16, 10, 4),
        "base-card-03": (16, 10, 6, 3),
        "base-card-04": (16, 10, 5),
        "base-card-05": (15, 10, 6, 4),
        "base-card-06": (13, 8, 4, 2),
        "base-card-07": (16, 10, 4),
        "base-card-08": (16, 10, 5),
        "base-card-09": (17, 10, 5),
        "base-card-10": (17, 10, 5),
        "base-card-11": (15, 9, 4),
        "base-card-12": (12, 5),
        "base-card-13": (18, 8),
        "base-card-14": (11, 5),
        "base-card-15": (17, 10, 5),
        "base-card-16": (14, 9, 4),
        "base-card-17": (13, 8, 4),
        "base-card-18": (15, 10, 6, 3),
        "base-card-19": (16, 10, 4),
        "base-card-20": (18, 11, 5),
        "base-card-21": (16, 10, 4),
        "base-card-22": (15, 10, 6, 3),
        "base-card-23": (16, 9, 4),
        "base-card-24": (11, 5),
        "base-card-25": (11, 5),
        "base-card-26": (14, 9, 5, 2),
        "base-card-27": (9, 4),
        "base-card-28": (12, 5),
        "base-card-29": (17, 10, 5),
        "base-card-30": (12, 6),
        "base-card-31": (17, 12, 8, 5),
        "base-card-32": (10, 5),
    }


def test_loaded_cards_use_recognizable_names() -> None:
    deck = load_base_animal_deck()

    assert all(not card.name.startswith("Base Card") for card in deck)
    assert deck[0].name == "Crocodile"
    assert deck[8].name == "Mouse"
    assert deck[24].name == "Condor"
    assert deck[31].name == "Panther"


def test_loaded_base_deck_can_start_a_game() -> None:
    state = GameRules.create_game(
        player_count=2,
        board_side=BoardSide.A,
        bag=build_bag(),
        animal_deck=load_base_animal_deck(),
    )

    assert len(state.animal_row) == 5
    assert len(state.animal_deck) == 27
