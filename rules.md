# Harmonies Rules

This file is a clean rewrite of the base rules for Harmonies. It is written for implementation and testing, not as a verbatim transcription of the published rulebook.

## Goal

Build a landscape on your personal board, complete animal habitats, and score more points than the other players.

Points come from two sources:

- Landscape scoring for terrain formations on your board.
- Animal card scoring based on how many cubes you place from each card.

## Components

- 1 central board with 5 terrain offers in multiplayer.
- 1 bag of terrain tokens.
- Terrain tokens in 6 colors:
  - Blue: water
  - Gray: mountains
  - Brown: trunks / woody trees
  - Green: foliage / treetops
  - Yellow: fields
  - Red: buildings
- Animal cards.
- Animal cubes.
- Personal boards with side A and side B.

## Setup

1. Put all terrain tokens in the bag.
2. Fill each of the 5 spaces on the central board with 3 tokens.
3. Reveal 5 animal cards.
4. Give each player a personal board. All players must use the same side.
5. Choose a first player.

## Turn Structure

On your turn, you must perform the mandatory action and may perform the optional actions.

Mandatory action:

- Draft 1 set of 3 terrain tokens from the central board and place all 3 on your board.

Optional actions:

- Take 1 animal card.
- Place animal cubes for any habitats you have completed.

These actions can be interleaved during the turn. For example, after placing one drafted token you may take an animal card, place another token, place an animal cube, and then place the last token.

At the end of your turn:

1. Refill the emptied terrain offer with 3 tokens.
2. Refill the animal card row back to 5 face-up cards.

## Animal Cards

Each animal card defines:

- A habitat pattern.
- The number of cubes available on the card.
- The token in the pattern that receives the cube.
- A score ladder based on how many cubes you managed to place.

Rules for animal cards:

- You may take at most 1 animal card per turn.
- You may have at most 4 active animal cards at once.
- When you take a card, place its cubes on the card.
- When you complete the habitat pattern, move the next cube from the card onto the indicated token on your board.
- The target token for the cube must not already have a cube on it.
- A token can help satisfy more than one habitat.
- Once a cube is placed, it stays on the board even if later placements break the original pattern.
- Once all cubes from a card are placed, the card is completed and no longer counts toward the 4-card hand limit.

## Token Placement Rules

General rules:

- A token may be placed on an empty space.
- A token may never be placed underneath an existing token.
- A token may not be placed on a space that already contains an animal cube.
- Stack height can never exceed 3.

Color-specific rules:

- Blue and yellow tokens can only be placed on empty spaces.
- Gray tokens can only be stacked on gray tokens, up to height 3.
- Brown tokens can be placed on empty spaces or stacked on brown tokens, up to height 2.
- Green tokens can be placed on empty spaces or on top of 1 or 2 brown tokens.
- Red tokens can only be placed on top of a single gray, brown, or red token. A red token is always the second token in the stack.

## Habitat Matching Rules

- Habitat patterns may be rotated.
- Mountain heights must match exactly.
- Tree heights must match exactly.
- Building spaces in habitats are satisfied by a red token on top of a legal base token.

## End of Game

The game ends when either of these happens at the end of a turn:

- The bag does not contain enough tokens to refill the emptied offer.
- A player has 2 or fewer empty spaces left on their board.

Finish the round so all players have taken the same number of turns.

## Scoring

### Trees

Trees are stacks with a green top.

- Height 1: 1 point
- Height 2: 3 points
- Height 3: 7 points

### Mountains

Mountains are gray stacks.

- Height 1: 1 point
- Height 2: 3 points
- Height 3: 7 points

A mountain scores only if it is adjacent to at least one other mountain. Otherwise it scores 0.

### Fields

Each connected yellow group of size 2 or more scores 5 points.

### Water

Side A:

- Only your best river scores.
- River score is based on the longest shortest path through connected blue tokens.
- 1 token: 0 points
- 2 tokens: 2 points
- 3 tokens: 5 points
- 4 tokens: 8 points
- 5 tokens: 11 points
- 6 tokens: 15 points
- Each token beyond 6: +4 points

Side B:

- Each island scores 5 points.
- An island is a connected group of non-blue board spaces separated from other groups by blue tokens.

### Buildings

Each building is worth 5 points if:

- It is a red token on top of a legal base token.
- It is adjacent to at least 3 different neighboring top colors.

Only the top visible token of each adjacent space counts.

### Animal Cards

Each animal card scores the highest uncovered value on that card.

- A card with no cubes placed scores 0.
- You do not sum all revealed values.

## Tie-breaker

If players tie on points, the tied player with more placed animal cubes wins. If still tied, the tie remains.

## Current Scope In This Repo

The current implementation scope is only the base multiplayer game. Solo mode, Nature's Spirit cards, low-vision cards, and custom variants are intentionally deferred until the core engine is stable.
