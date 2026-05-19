
# --- Логические константы ---
MIN_ROWS = 5
MIN_COLS = 5
MIN_FREE_CELLS = 9

STANDARD_ROWS = 10
STANDARD_COLS = 10
STANDARD_MINES = 30

NEIGHBOR_OFFSETS = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


# --- Визуальные константы ---
FLAG_EMOJI = "🚩"
MINE_EMOJI = "💣"
NUMBER_COLORS = {
    1: "blue",
    2: "green",
    3: "red",
    4: "darkblue",
    5: "maroon",
    6: "teal",
    7: "black",
    8: "gray",
}
OPEN_BG = "#e0e0e0"
MINE_BG = "#ff6b6b"
HINT_SAFE_BG = "#b8e6b8"
HINT_MINE_BG = "#f5b0b0"
HINT_HIGHLIGHT_MS = 1500
