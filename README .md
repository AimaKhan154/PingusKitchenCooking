# 🐧 Pingu's Cozy Kitchen

> A cozy penguin cooking game built entirely in Python + Pygame — no assets required.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Requirements & Installation](#requirements--installation)
- [How to Run](#how-to-run)
- [How to Play](#how-to-play)
- [Level System](#level-system)
- [Ingredients & Recipes](#ingredients--recipes)
- [Scoring](#scoring)
- [Controls](#controls)
- [Music & Audio](#music--audio)
- [Code Architecture](#code-architecture)
- [Class Reference](#class-reference)
- [Visual Systems](#visual-systems)
- [File Structure](#file-structure)

---

## Screenshot

<img width="1576" height="985" alt="image" src="https://github.com/user-attachments/assets/e74ee4c0-7fcf-4e04-b8cd-6e3342a6382d" />
<img width="1572" height="967" alt="image" src="https://github.com/user-attachments/assets/b19bcbc2-856a-4ffa-a513-ca7d602a14ee" />
<img width="1585" height="1000" alt="image" src="https://github.com/user-attachments/assets/23ba11a3-ccb9-4de4-8fae-295eabe57653" />
<img width="1585" height="997" alt="image" src="https://github.com/user-attachments/assets/88bd3a96-9623-4ed9-8ca4-d9befa3c2442" />

---
## Overview

Pingu's Cozy Kitchen is a single-file arcade cooking game where you play as a penguin chef. Orders appear at the top of the screen — click ingredients in the correct order and hit **SERVE** before time runs out. Miss too many orders or fail to hit the level score target and it's game over.

The entire game — graphics, sound effects, background music, animations, and UI — is generated procedurally in pure Python. No external image or audio assets are needed (though you can drop in a real MP3 for music).

---

## Requirements & Installation

**Python 3.8+** and **Pygame** are the only dependencies.

```bash
pip install pygame
```

That's it. No other packages needed.

---

## How to Run

```bash
python pinguKictchen.py
```

The game window opens at **1280 × 780** and is resizable.

### Optional: Real Music

Place the music file `Penguins Parade on the Frozen Shore.mp3` in the **same folder** as the script. The game will automatically detect and use it. Without it, a procedurally generated pentatonic café loop plays instead.

The game also checks for these filenames as fallbacks:
- `penguin_parade.mp3`
- `penguin_parade.wav`

---

## How to Play

```
┌─────────────────────────────────────────────┐
│  INCOMING ORDERS (top)         HUD (right)  │
├──────────┬──────────────────────────────────┤
│          │                                  │
│ INGREDS  │        ORDER CARDS               │
│  (left)  │                                  │
│          │                                  │
│          │      MIXING BOWL (centre)        │
│          │      [SERVE ▲]  [✕ clear]        │
└──────────┴──────────────────────────────────┘
```

1. **Read an order card** at the top — it shows the dish name, required ingredients in numbered order, and a countdown timer ring.
2. **Click ingredients** on the left panel in the exact order shown on the card.
3. **Click SERVE** when your bowl matches an order exactly.
4. **Click ✕** to remove the last ingredient from the bowl if you made a mistake.
5. Earn points, build combos, and advance through 5 levels!

### Losing Conditions
- **5 expired orders** in a single level → Game Over
- **Time runs out** before reaching the level's score target → Game Over

---

## Level System

The game has **5 discrete levels**. Each level has its own countdown timer and a score target you must hit to advance. When you clear a level, a **Level Complete screen** appears for ~3.5 seconds before the next level begins.

| Level | Duration | Score Target | Title              | Fails Reset? |
|-------|----------|-------------|--------------------|-------------|
| 1     | 60 sec   | 80 pts      | Apprentice Chef 🐣  | ✅ Yes      |
| 2     | 70 sec   | 180 pts     | Sous Chef 🐧        | ✅ Yes      |
| 3     | 75 sec   | 320 pts     | Head Chef 🎩        | ✅ Yes      |
| 4     | 80 sec   | 500 pts     | Master Chef ⭐      | ✅ Yes      |
| 5     | 90 sec   | 750 pts     | Legendary Pingu 👑  | ✅ Yes      |

- **Fails reset** to 0 at the start of each new level.
- **Score is cumulative** across all levels — the target is measured against points earned *within* the current level.
- Higher levels spawn orders faster and unlock harder (more ingredient) recipes.
- Beating Level 5 triggers the animated **YOU WIN!** end screen.

### Level Progress Bar (HUD)

The right-side HUD panel shows a progress bar that fills from red → green as you earn points toward the current level's score target. The label reads `Lvl goal  X / Y`.

---

## Ingredients & Recipes

Ingredients and recipes are **locked** at the start and unlock as you advance levels. Locked ingredients appear greyed out with a **LOCKED** label.

### Ingredients

| Name       | Unlocks | Colour      |
|------------|---------|-------------|
| Salmon     | Lv 1    | Coral       |
| Rice       | Lv 1    | Light blue  |
| Avocado    | Lv 1    | Green       |
| Ice        | Lv 1    | Cyan        |
| Mango      | Lv 2    | Amber       |
| Cream      | Lv 2    | Cream       |
| Boba       | Lv 2    | Brown       |
| Chocolate  | Lv 3    | Dark brown  |
| Shrimp     | Lv 3    | Orange      |
| Seaweed    | Lv 3    | Dark green  |
| Cheese     | Lv 4    | Yellow      |
| Squid      | Lv 4    | Purple      |
| Strawberry | Lv 5    | Red/pink    |
| Krill      | Lv 5    | Crimson     |

### Recipes (17 total)

| Dish           | Unlocks | Stars | Time  | Ingredients                            |
|----------------|---------|-------|-------|----------------------------------------|
| Poke Bowl      | Lv 1    | ⭐    | 18s   | Salmon → Rice → Avocado               |
| Salmon Chill   | Lv 1    | ⭐    | 15s   | Salmon → Rice → Ice                   |
| Avo Chill      | Lv 1    | ⭐    | 14s   | Avocado → Ice → Rice                  |
| Mango Shake    | Lv 2    | ⭐    | 16s   | Mango → Cream → Ice                   |
| Bubble Tea     | Lv 2    | ⭐    | 15s   | Boba → Cream → Ice                    |
| Mango Cream    | Lv 2    | ⭐⭐  | 18s   | Mango → Cream → Boba                  |
| Avo Bowl       | Lv 2    | ⭐⭐  | 19s   | Avocado → Rice → Mango                |
| Sushi Bowl     | Lv 3    | ⭐⭐  | 20s   | Salmon → Rice → Seaweed               |
| Choco Dream    | Lv 3    | ⭐⭐  | 18s   | Choco → Cream → Boba                  |
| Ramen Bowl     | Lv 3    | ⭐⭐  | 22s   | Shrimp → Seaweed → Rice               |
| Protein Bowl   | Lv 3    | ⭐⭐⭐ | 25s  | Salmon → Avocado → Shrimp → Rice      |
| Ice Cream      | Lv 4    | ⭐⭐  | 16s   | Cream → Choco → Ice                   |
| Cheese Ramen   | Lv 4    | ⭐⭐⭐ | 24s  | Cheese → Shrimp → Seaweed → Rice      |
| Squid Ink      | Lv 4    | ⭐⭐  | 20s   | Squid → Seaweed → Rice                |
| Milkshake      | Lv 5    | ⭐⭐  | 16s   | Cream → Strawberry → Ice              |
| Mocktail       | Lv 5    | ⭐⭐⭐ | 22s  | Mango → Strawberry → Cream → Ice      |
| Polar Plate    | Lv 5    | ⭐⭐⭐ | 26s  | Salmon → Krill → Squid → Seaweed      |

> **Order matters!** Ingredients must be added in exactly the listed sequence.

---

## Scoring

| Action             | Points                                           |
|--------------------|--------------------------------------------------|
| Correct serve      | `stars × 20 × (0.5 + time_remaining_ratio)`     |
| Combo multiplier   | `base_pts × (1 + combo × 0.25)` for combo ≥ 2  |
| Wrong serve        | 0 pts, combo resets                              |
| Expired order      | 0 pts, fail count +1, combo resets              |

- **Combo** builds by serving consecutive correct orders without any wrong serves or expirations.
- A combo of x2 or higher shows a pulsing `xN COMBO!` badge in the HUD and plays a special chord sound.
- Serving quickly (while more time remains on the order card) gives a higher point multiplier.

---

## Controls

| Input              | Action                         |
|--------------------|--------------------------------|
| **Left Click**     | Click ingredient / SERVE / ✕   |
| **R**              | Restart game from Level 1      |
| **ESC**            | Quit immediately               |

The ✕ button removes only the **last** ingredient added (one at a time undo). Clicking during the Level Complete interstitial is disabled — just wait for the next level to start.

---

## Music & Audio

### Background Music
The game first looks for a real MP3/WAV file (see [How to Run](#how-to-run)). If none is found, it generates a **procedural pentatonic café loop** at runtime using raw sine waves:

- 80 BPM, 8 bars, pentatonic scale
- Soft melody + gentle bass line
- Built entirely with `struct.pack` into a pygame Sound buffer

### Sound Effects

| Event           | Sound                        |
|-----------------|------------------------------|
| Add ingredient  | Short high sine `pop`        |
| Correct serve   | Major chord jingle           |
| Combo serve     | Extended 4-note chord        |
| Wrong serve     | Low descending tone          |
| Order expired   | Mid descending tone          |
| Level up        | Bright ascending arpeggio    |
| Button click    | Very short high tick         |

All SFX are procedurally generated using sine waves with simple attack/decay envelopes. If audio init fails (e.g. no sound device), the game runs silently without crashing.

---

## Code Architecture

The entire game is a **single Python file** (~1,600 lines). It is organized into these sections:

```
pinguKictchen.py
│
├── INIT          — pygame init, window, clock, audio setup
├── MUSIC LOADER  — tries real MP3, falls back to procedural BGM
├── HELPERS       — lerp, clamp, lerp_color math utilities
├── PALETTE       — global colour constants
├── FONT LOADER   — system font fallback chain
├── DRAW PRIMITIVES
│     draw_glass()      — frosted glass panel (SRCALPHA rect)
│     draw_ring()       — circular timer arc
│     draw_btn()        — styled button
│     glow_dot()        — small glowing circle
├── SOUND GENERATION
│     _sine_buf()       — single sine-wave buffer
│     _chord_buf()      — multi-frequency chord buffer
│     _bgm_buf()        — full procedural BGM loop
│     sfx()             — safe sound player
├── DATA
│     INGREDIENTS[]     — 14 ingredients with unlock levels & colours
│     RECIPES[]         — 17 recipes with unlock levels, stars, times
│     IMAP{}            — short-key lookup dict for ingredients
├── ICON RENDERER       — _make_icon() draws each ingredient procedurally
├── BACKGROUND BUILDER  — _build_bg() vertical gradient, baked to surface
│
├── CLASS: Penguin       — animated chef penguin (bob, blink, dance, hat)
├── CLASS: Particle      — burst particle with gravity
├── CLASS: FloatText     — rising score/combo label animation
├── CLASS: DropAnim      — arc-path ingredient drop into bowl
├── CLASS: OrderCard     — order ticket with countdown ring
├── CLASS: IngBtn        — ingredient button with press/hover/locked state
├── CLASS: Stars         — twinkling background star field
├── CLASS: Aurora        — animated aurora borealis waves
├── CLASS: Snowflake     — falling snow particles
│
├── HELPERS (end-screen)
│     _draw_outlined_text()   — text with drop shadow
│     _draw_gradient_rect()   — vertical gradient rounded rect
│
├── CLASS: EndScreen     — animated win/lose full-screen overlay
│
├── CLASS: Game          — main game controller
│     reset()             — full restart to Level 1
│     unlocked()          — set of currently available ingredient shorts
│     speed()             — order speed multiplier based on level
│     spawn_order()       — pick random available recipe, create OrderCard
│     emit()              — burst particles at position
│     add_float()         — create floating score label
│     try_serve()         — validate bowl against orders; score/level logic
│     handle_click()      — route mouse clicks to buttons/serve/clear
│     update()            — per-frame game state machine
│     draw()              — master draw call (12+ layers)
│     _draw_topbar()      — title bar
│     _draw_left_panel()  — ingredient buttons panel
│     _draw_orders()      — order cards row
│     _draw_bowl()        — mixing bowl + serve/clear buttons
│     _draw_hud()         — score, level, fails, progress, timer
│     _draw_gameover()    — delegates to EndScreen
│     _draw_level_complete() — between-level interstitial overlay
│
└── MAIN LOOP            — event pump → game.update() → game.draw() @ 60 FPS
```

---

## Class Reference

### `Game`

The central controller. Key attributes:

| Attribute            | Type    | Description                                      |
|----------------------|---------|--------------------------------------------------|
| `score`              | int     | Cumulative score across all levels               |
| `level`              | int     | Current level (1–5)                              |
| `level_score_start`  | int     | Score value at the start of the current level    |
| `GAME_DUR`           | float   | Countdown duration for the current level (secs)  |
| `game_t`             | float   | Elapsed time in the current level                |
| `failed_count`       | int     | Expired orders this level (resets per level)     |
| `combo`              | int     | Current consecutive correct serves               |
| `stars_earned`       | int     | Total stars earned (cosmetic)                    |
| `level_complete`     | bool    | True while the level-complete interstitial shows |
| `orders`             | list    | Active `OrderCard` instances (max 4)             |
| `bowl`               | list    | Ingredient shorts currently in the mixing bowl   |

`LEVEL_CONFIG` is a class-level tuple of `(duration, score_target, title_label)` for each of the 5 levels.

---

### `Penguin`

Fully procedural animated character. No sprites used.

- **`react_happy()`** — triggers bouncing + dancing + sparkles for 1.6 seconds
- **`react_sad()`** — triggers blue cheeks + tear drop for 1.4 seconds
- **`outfit`** — integer 0–4 controlling the hat band colour (changes per level)
- Blinks randomly every 2–5 seconds
- Gently bobs on a sine wave at all times

---

### `OrderCard`

One active customer order.

- **`recipe`** — dict with `name`, `ing` (list of shorts), `stars`, `time`, `unlock`
- **`remain`** / **`total`** — time left vs original time (affected by level speed)
- **`done`** / **`failed`** — state flags
- Card slides in from above on spawn and fades out on completion

---

### `EndScreen`

Full-screen animated overlay for win or game-over.

- Rainbow letter-by-letter "YOU WIN!" headline on win
- Wobbly red "GAME OVER" on loss
- Displays final score, stars, level reached, and chef grade (S / A / B / C / D)
- Floating decorative symbols (stars, hearts, snowflakes, fish, notes)
- Side penguins + corner fish decorations
- Prompts **R** to restart

---

### `Aurora`, `Stars`, `Snowflake`

Background atmosphere classes. All update every frame but are lightweight:

- `Aurora` redraws its surface only every **6 frames** (optimization)
- `Stars` are static positions that twinkle via sine brightness
- `Snowflake` respawns at the top when it drifts off the bottom

---

## Visual Systems

### Glass Panels
`draw_glass()` creates frosted-glass-style UI panels using a single `SRCALPHA` surface per call with optional border and glow. Used for the ingredient panel, HUD, order cards, bowl, and buttons.

### Procedural Icons
Each ingredient has a unique hand-coded icon drawn with pygame primitives (polygons, ellipses, circles, lines). Icons are rendered **once at startup** into two cached dictionaries: `ICONS` (44px) and `ICONS_SM` (26px).

### Particle System
Three types of particle-like objects coexist:
- `Particle` — physics-driven burst dots with gravity
- `FloatText` — rising score/combo labels that fade out
- `DropAnim` — arc-path icon animation from button → bowl

### Background
A vertical gradient surface is baked once into `BG_SURF` at startup (no per-frame cost) and blitted as the first draw call each frame.

---

## File Structure

```
📁 your-folder/
├── pinguKictchen.py                          ← the entire game
└── Penguins Parade on the Frozen Shore.mp3   ← optional real music
```

Everything else is generated at runtime. No asset folders, no config files.

---

## Tips & Tricks

- **Speed matters** — serving an order while lots of time remains gives a big bonus multiplier.
- **Build combos** — each consecutive correct serve multiplies your score. A x5 combo can triple your points per dish.
- **Undo with ✕** — if you click the wrong ingredient, hit ✕ to remove just the last one. You don't have to clear the whole bowl.
- **Watch the urgency** — order card borders flash red when time is nearly up. Prioritise those over new orders.
- **Level 3 is the gear shift** — 4-ingredient recipes unlock here. Memorise Protein Bowl (`salmon → avocado → shrimp → rice`) early.
- **Fail counter resets per level** — don't stress about one or two misses; just focus on hitting the score target.

---

*Made with 🐧 and pure Python.*
