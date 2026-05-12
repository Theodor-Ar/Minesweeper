"""Запуск игры."""

import tkinter as tk

from src.core.logic import MinesweeperLogic
from src.ui.gui import MinesweeperGUI


ROWS = 10
COLS = 10
MINES = 10


def main() -> None:
    root = tk.Tk()
    root.title("Сапёр")
    root.resizable(False, False)

    game_logic = MinesweeperLogic(rows=ROWS, cols=COLS, mines=MINES)
    MinesweeperGUI(root=root, game_logic=game_logic)

    root.mainloop()


if __name__ == "__main__":
    main()
