# harmonies-ext

This repo is for implementing the board game Harmonies, then extending it with new cards, terrains, and other variants.

## Current Status

The first implementation pass is a Python rules engine for the base multiplayer game:

- terrain placement rules
- habitat matching
- animal card progression
- endgame handling
- scoring for trees, mountains, fields, water, buildings, and animal cards

The current scope intentionally excludes solo mode, Nature's Spirit cards, and low-vision or custom card packs.

## Files

- `rules.md`: implementation-oriented rules rewrite for the base game
- `src/harmonies/`: engine code
- `tests/`: placement, scoring, and turn-flow tests

## Running Tests

```bash
python -m pytest
```

## Design Notes

- The engine is deterministic by default. Bag order and animal deck order are passed in directly so tests stay stable.
- The personal board layout is injected into the game setup. Official layouts can be encoded later without rewriting the core rules logic.
