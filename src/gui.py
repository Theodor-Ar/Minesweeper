"""GUI на Tkinter."""

import tkinter as tk
from typing import List

from src.logic import MinesweeperLogic


class MinesweeperGUI:
    """Окно и сетка кнопок."""

    def __init__(self, root: tk.Tk, game_logic: MinesweeperLogic) -> None:
        self.root = root
        self.logic = game_logic
        self.buttons: List[List[tk.Button]] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создать сетку кнопок и навесить обработчики мыши."""
        for r in range(self.logic.rows):
            row_buttons: List[tk.Button] = []
            for c in range(self.logic.cols):
                button = tk.Button(
                    self.root,
                    width=2,
                    height=1,
                    font=("Helvetica", 12, "bold"),
                )
                button.grid(row=r, column=c, padx=0, pady=0)
                button.bind(
                    "<Button-1>",
                    lambda event, row=r, col=c: self._on_left_click(row, col),
                )
                button.bind(
                    "<Button-3>",
                    lambda event, row=r, col=c: self._on_right_click(row, col),
                )
                row_buttons.append(button)
            self.buttons.append(row_buttons)

    def _on_left_click(self, row: int, col: int) -> None:
        """ЛКМ: открыть клетку и перерисовать поле."""
        pass

    def _on_right_click(self, row: int, col: int) -> None:
        """ПКМ: переключить флаг."""
        pass
