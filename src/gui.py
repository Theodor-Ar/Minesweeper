"""GUI на Tkinter."""

import sys
import tkinter as tk
from tkinter import messagebox

from src.logic import MinesweeperLogic

FLAG_EMOJI = "🚩"
MINE_EMOJI = "💣"

NUMBER_COLORS: dict[int, str] = {
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

# Фиксированный размер клетки в пикселях (не зависит от текста/emoji).
CELL_SIZE_PX = 36


def _emoji_font() -> tuple[str, int]:
    if sys.platform == "darwin":
        return ("Apple Color Emoji", 14)
    if sys.platform == "win32":
        return ("Segoe UI Emoji", 14)
    return ("Noto Color Emoji", 14)


class MinesweeperGUI:
    """Окно и сетка кнопок."""

    def __init__(self, root: tk.Tk, game_logic: MinesweeperLogic) -> None:
        self.root = root
        self.logic = game_logic
        self.buttons: list[list[tk.Button]] = []
        self._font_cell = ("Helvetica", 13, "bold")
        self._font_emoji = _emoji_font()

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создать сетку кнопок и навесить обработчики мыши."""
        toolbar = tk.Frame(self.root)
        toolbar.grid(row=0, column=0, columnspan=self.logic.cols, pady=(0, 4))

        tk.Button(toolbar, text="Новая игра", command=self._restart).pack()

        board_frame = tk.Frame(self.root)
        board_frame.grid(row=1, column=0)

        for r in range(self.logic.rows):
            row_buttons: list[tk.Button] = []
            for c in range(self.logic.cols):
                cell_frame = tk.Frame(
                    board_frame,
                    width=CELL_SIZE_PX,
                    height=CELL_SIZE_PX,
                )
                cell_frame.grid(row=r, column=c, padx=0, pady=0)
                cell_frame.grid_propagate(False)

                button = tk.Button(
                    cell_frame,
                    font=self._font_cell,
                    padx=0,
                    pady=0,
                    borderwidth=1,
                    highlightthickness=0,
                    anchor="center",
                    justify="center",
                )
                button.place(relx=0, rely=0, relwidth=1, relheight=1)
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

        self._refresh_board()

    def _restart(self) -> None:
        self.logic.reset()
        self._refresh_board()

    def _refresh_board(self) -> None:
        if self.logic.is_game_over and not self.logic.is_won:
            self.logic.reveal_all_mines()

        for r in range(self.logic.rows):
            for c in range(self.logic.cols):
                self._update_button(r, c)

    def _update_button(self, row: int, col: int) -> None:
        btn = self.buttons[row][col]
        cell = self.logic.board[row][col]

        if cell["is_open"]:
            btn.config(relief=tk.SUNKEN, state=tk.DISABLED)
            if cell["is_mine"]:
                btn.config(
                    text=MINE_EMOJI,
                    font=self._font_emoji,
                    bg=MINE_BG,
                    fg="black",
                )
            elif cell["neighbors"] == 0:
                btn.config(
                    text="",
                    font=self._font_cell,
                    bg=OPEN_BG,
                    fg="black",
                )
            else:
                n = cell["neighbors"]
                btn.config(
                    text=str(n),
                    font=self._font_cell,
                    bg=OPEN_BG,
                    fg=NUMBER_COLORS[n],
                )
            return

        btn.config(
            relief=tk.RAISED,
            state=tk.NORMAL,
            bg="SystemButtonFace",
            fg="black",
            font=self._font_cell,
        )
        if cell["is_flagged"]:
            btn.config(text=FLAG_EMOJI, font=self._font_emoji)
        else:
            btn.config(text="")

    def _on_left_click(self, row: int, col: int) -> None:
        """ЛКМ: открыть клетку и перерисовать поле."""
        if self.logic.is_game_over:
            return

        self.logic.open_cell(row, col)
        self._refresh_board()

        if self.logic.is_game_over:
            if self.logic.is_won:
                messagebox.showinfo("Сапёр", "Победа!")
            else:
                messagebox.showinfo("Сапёр", "Поражение!")

    def _on_right_click(self, row: int, col: int) -> None:
        """ПКМ: переключить флаг."""
        if self.logic.is_game_over:
            return

        self.logic.toggle_flag(row, col)
        self._update_button(row, col)
