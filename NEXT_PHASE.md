# Next Phase

The first implementation pass established a working base engine for multiplayer rules, scoring, and turn flow. The next phase should turn that scaffold into a more complete game model with real content and stronger validation.

## Goal

Move from a generic rules engine to a faithful implementation of the base game with official board layouts and real animal card data.

## Scope

- Add official personal board layouts instead of relying on injected test layouts.
- Add a data-driven catalog of the base animal cards.
- Extend tests so they validate real card patterns and real board constraints.
- Keep the scope limited to the standard multiplayer game.

## Main Work Items

1. Encode the A and B personal board layouts as reusable board definitions.
2. Add a card data file format for animal definitions.
3. Load the full base deck from data instead of constructing cards in tests only.
4. Add fixture-based tests for representative animal cards and scoring combinations.
5. Add one higher-level integration test that simulates a short real game setup and a few turns.

## Not In Scope Yet

- Solo mode
- Nature's Spirit cards
- Low-vision card pack
- Custom terrains or custom cards
- UI work

## Exit Criteria

This phase is complete when:

- the engine can start a game with official board layouts,
- the base animal deck is loaded from data,
- the tests cover real card behavior instead of only synthetic examples,
- and the existing multiplayer rules still pass cleanly.
