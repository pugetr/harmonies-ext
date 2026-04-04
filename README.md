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

The base animal deck is now loaded from packaged JSON data derived from the simplified card resources.

## Running Tests

```bash
python -m pytest
```

## Install

Create and activate a virtual environment, then install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

If you also want the test dependencies:

```bash
python -m pip install -e .[dev]
```

## Run The Game

The playable interface is now a persistent full-screen terminal UI for a local two-player hotseat game.

After installation, launch it with:

```bash
harmonies-play
```

You can also run it directly from the source tree without installing the console script:

```bash
PYTHONPATH=src python -m harmonies.cli
```

The interface runs in the terminal alternate screen and keeps the board, offers, animal row, active cards, cursor details, and the latest action message visible at once.

The playable app shuffles the terrain bag on startup, so the draft offers are randomized each game. The rules engine still accepts an explicit bag order directly when you want deterministic tests or scripted scenarios.

Core controls:

- Arrow keys or `hjkl`: move the board cursor
- `o`: cycle drafted-offer selection
- `n`: cycle animal-row selection
- `c`: cycle active animal cards
- `r`: rotate the current animal habitat preview
- `d`: draft the selected offer
- `t`: take the selected animal card
- `Enter`, `Space`, or `p`: place the next terrain token or the previewed animal cube
- `e`: end the turn
- `q`: quit the session

The board view highlights legal token placements or legal animal anchors for the currently selected card and rotation. When a cube placement is possible, the preview target is shown directly on the board.

## Design Notes

- The engine is deterministic by default. Bag order and animal deck order are passed in directly so tests stay stable.
- Game setup now uses reusable official personal board definitions keyed by board side.
