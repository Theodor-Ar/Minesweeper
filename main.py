"""Запуск игры."""

import tkinter as tk

from src.gui import MinesweeperGUI
from src.logic import MinesweeperLogic
from src.config import STANDARD_COLS, STANDARD_MINES, STANDARD_ROWS


def main() -> None:
    root = tk.Tk()
    root.title("Сапёр")
    root.resizable(False, False)

    game_logic = MinesweeperLogic(
        rows=STANDARD_ROWS,
        cols=STANDARD_COLS,
        mines=STANDARD_MINES,
    )
    MinesweeperGUI(root=root, game_logic=game_logic)

    root.mainloop()


if __name__ == "__main__":
    main()
