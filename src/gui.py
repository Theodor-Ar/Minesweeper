"""GUI на Tkinter."""

import sys
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox
from src.config import *
from src.logic import MinesweeperLogic


@dataclass(frozen=True)
class Layout:
    """Единый расчёт размеров: сетка клеток → контент → окно."""

    cell_px: int = 36
    outer_pad: int = 12  # единый отступ content_frame от краёв окна (padx/pady у grid)
    panel_gap: int = 8  # зазор между панелью управления и полем
    chrome_w: int = 12  # системные рамки окна по ширине
    chrome_h: int = 28  # заголовок и нижняя рамка
    screen_edge_w: int = 12
    screen_edge_h: int = 20
    geom_tol: int = 4
    min_window: int = 200

    def board_pixels(self, rows: int, cols: int) -> tuple[int, int]:
        """Только сетка клеток, без внешних отступов."""
        return cols * self.cell_px, rows * self.cell_px

    def inner_pixels(
        self, rows: int, cols: int, panel_w: int, panel_h: int
    ) -> tuple[int, int]:
        """Панель + зазор + поле внутри content_frame."""
        board_w, board_h = self.board_pixels(rows, cols)
        return max(panel_w, board_w), panel_h + self.panel_gap + board_h

    def window_pixels(
        self, rows: int, cols: int, panel_w: int, panel_h: int
    ) -> tuple[int, int]:
        """inner + 2 x outer_pad + chrome."""
        iw, ih = self.inner_pixels(rows, cols, panel_w, panel_h)
        return (
            iw + 2 * self.outer_pad + self.chrome_w,
            ih + 2 * self.outer_pad + self.chrome_h,
        )


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
        self.layout = Layout()
        self.buttons: list[list[tk.Button]] = []
        self._font_cell = ("Helvetica", 13, "bold")
        self._font_emoji = _emoji_font()

        self._timer_seconds = 0
        self._timer_running = False
        self._timer_after_id: str | None = None
        self._hint_after_id: str | None = None
        self._hint_cell: tuple[int, int] | None = None

        self._mode_var = tk.StringVar(value="standard")
        self._rows_var = tk.StringVar(value=str(STANDARD_ROWS))
        self._cols_var = tk.StringVar(value=str(STANDARD_COLS))
        self._mines_var = tk.StringVar(value=str(STANDARD_MINES))

        ly = self.layout
        self._content_frame = tk.Frame(self.root)
        self._content_frame.grid(
            row=0,
            column=0,
            padx=ly.outer_pad,
            pady=ly.outer_pad,
        )

        self._create_controls()
        self._board_frame = tk.Frame(self._content_frame)
        self._board_frame.grid(row=1, column=0, pady=(ly.panel_gap, 0))
        self._build_board()
        self._on_mode_change()
        self._apply_window_geometry()

    # --- Панель управления ---

    def _create_controls(self) -> None:
        panel = tk.Frame(self._content_frame, padx=4, pady=4)
        panel.grid(row=0, column=0, sticky="w")
        self._control_panel = panel

        mode_frame = tk.LabelFrame(panel, text="Режим новой игры", padx=6, pady=4)
        mode_frame.pack(fill="x", pady=(0, 6))
        for text, value in (("Стандартная игра", "standard"), ("Свои настройки", "custom")):
            tk.Radiobutton(
                mode_frame,
                text=text,
                variable=self._mode_var,
                value=value,
                command=self._on_mode_change,
            ).pack(anchor="w")

        custom = tk.Frame(mode_frame)
        custom.pack(fill="x", pady=(4, 0))
        fields = (("Строки:", self._rows_var), ("Столбцы:", self._cols_var), ("Мины:", self._mines_var))
        self._custom_entries: list[tk.Entry] = []
        for col, (label, var) in enumerate(fields):
            tk.Label(custom, text=label).grid(row=0, column=col * 2, sticky="w")
            entry = tk.Entry(custom, width=5, textvariable=var)
            entry.grid(row=0, column=col * 2 + 1, padx=(4, 12 if col < 2 else 0))
            self._custom_entries.append(entry)

        actions = tk.Frame(panel)
        actions.pack(fill="x")
        tk.Button(actions, text="Новая игра", command=self._start_new_game).pack(side="left")
        self._timer_label = tk.Label(actions, text="Время: 000 с", width=14)
        self._timer_label.pack(side="left", padx=(12, 0))
        tk.Button(actions, text="Подсказка", command=self._show_hint).pack(side="left", padx=(8, 0))

    def _on_mode_change(self) -> None:
        state = tk.NORMAL if self._mode_var.get() == "custom" else tk.DISABLED
        for entry in self._custom_entries:
            entry.config(state=state)

    def _set_field_vars(self, rows: int, cols: int, mines: int) -> None:
        self._rows_var.set(str(rows))
        self._cols_var.set(str(cols))
        self._mines_var.set(str(mines))

    # --- Размеры и геометрия ---

    def _panel_size(self) -> tuple[int, int]:
        self._control_panel.update_idletasks()
        return self._control_panel.winfo_reqwidth(), self._control_panel.winfo_reqheight()

    def _window_size(self, rows: int, cols: int) -> tuple[int, int]:
        pw, ph = self._panel_size()
        return self.layout.window_pixels(rows, cols, pw, ph)

    def _actual_window_size(self) -> tuple[int, int]:
        self.root.update_idletasks()
        return self.root.winfo_width(), self.root.winfo_height()

    def _window_fits_field(self, rows: int, cols: int) -> bool:
        req_w, req_h = self._window_size(rows, cols)
        act_w, act_h = self._actual_window_size()
        tol = self.layout.geom_tol
        return act_w >= req_w - tol and act_h >= req_h - tol

    def _screen_limit(self) -> tuple[int, int]:
        self._control_panel.update_idletasks()
        try:
            sw, sh = self.root.winfo_vrootwidth(), self.root.winfo_vrootheight()
        except tk.TclError:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        lo = self.layout.min_window
        return (
            max(lo, sw - self.layout.screen_edge_w),
            max(lo, sh - self.layout.screen_edge_h),
        )

    def _fits_screen(self, rows: int, cols: int) -> bool:
        w, h = self._window_size(rows, cols)
        limit_w, limit_h = self._screen_limit()
        return w <= limit_w and h <= limit_h

    def _max_field_dimensions(self) -> tuple[int, int]:
        limit_w, limit_h = self._screen_limit()
        pw, ph = self._panel_size()
        ly = self.layout

        overhead = ph + ly.panel_gap + 2 * ly.outer_pad + ly.chrome_h
        max_rows = max(MIN_ROWS, (limit_h - overhead) // ly.cell_px)

        max_cols = MIN_COLS
        for cols in range(MIN_COLS, 5000):
            if self._window_size(max_rows, cols)[0] <= limit_w:
                max_cols = cols
            else:
                break

        while max_rows >= MIN_ROWS and not self._fits_screen(max_rows, max_cols):
            max_rows -= 1
        return max_rows, max_cols

    def _shrink_field_step(
        self, rows: int, cols: int, req_w: int, req_h: int, act_w: int, act_h: int
    ) -> tuple[int, int] | None:
        tol = self.layout.geom_tol
        if act_h < req_h - tol and rows > MIN_ROWS:
            return rows - 1, cols
        if act_w < req_w - tol and cols > MIN_COLS:
            return rows, cols - 1
        if rows > MIN_ROWS:
            return rows - 1, cols
        if cols > MIN_COLS:
            return rows, cols - 1
        return None

    def _clamp_to_screen(self, rows: int, cols: int, mines: int) -> tuple[int, int, int, bool]:
        rows, cols = max(rows, MIN_ROWS), max(cols, MIN_COLS)
        max_r, max_c = self._max_field_dimensions()
        adjusted = False
        if rows > max_r:
            rows, adjusted = max_r, True
        if cols > max_c:
            cols, adjusted = max_c, True
        mines = MinesweeperLogic.clamp_mines(rows, cols, mines)
        return rows, cols, mines, adjusted

    def _ensure_fits_window(
        self, rows: int, cols: int, mines: int
    ) -> tuple[int, int, int, bool]:
        rows, cols = max(rows, MIN_ROWS), max(cols, MIN_COLS)
        mines = MinesweeperLogic.clamp_mines(rows, cols, mines)
        adjusted = False

        for _ in range(rows + cols + 10):
            self.logic.new_game(rows, cols, mines)
            self._rebuild_board()
            self._apply_window_geometry()

            if self._window_fits_field(rows, cols):
                return rows, cols, mines, adjusted

            adjusted = True
            req_w, req_h = self._window_size(rows, cols)
            act_w, act_h = self._actual_window_size()
            step = self._shrink_field_step(rows, cols, req_w, req_h, act_w, act_h)
            if step is None:
                break
            rows, cols = step
            mines = MinesweeperLogic.clamp_mines(rows, cols, mines)

        return rows, cols, mines, adjusted

    def _apply_window_geometry(self) -> None:
        ly = self.layout
        board_w, board_h = ly.board_pixels(self.logic.rows, self.logic.cols)
        self._board_frame.config(width=board_w, height=board_h)
        self._board_frame.grid_propagate(False)

        self.root.minsize(1, 1)
        self._content_frame.update_idletasks()
        w, h = self._window_size(self.logic.rows, self.logic.cols)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.root.update_idletasks()

    # --- Запуск игры ---

    def _get_game_params(self) -> tuple[int, int, int] | None:
        if self._mode_var.get() == "standard":
            return STANDARD_ROWS, STANDARD_COLS, STANDARD_MINES

        try:
            rows = int(self._rows_var.get().strip())
            cols = int(self._cols_var.get().strip())
            mines = int(self._mines_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целые числа для строк, столбцов и мин.")
            return None

        ok, msg = MinesweeperLogic.validate_settings(rows, cols, mines)
        if not ok:
            messagebox.showerror("Ошибка", msg)
            return None

        rows, cols, mines, adjusted = self._clamp_to_screen(rows, cols, mines)
        if adjusted:
            self._set_field_vars(rows, cols, mines)
            messagebox.showinfo(
                "Размер поля",
                "Размеры уменьшены до максимально допустимых для вашего экрана:\n"
                f"{rows} строк × {cols} столбцов, {mines} мин.",
            )
        return rows, cols, mines

    def _start_new_game(self) -> None:
        params = self._get_game_params()
        if params is None:
            return

        rows, cols, mines = params
        self._clear_hint_highlight()
        self._reset_timer()

        rows, cols, mines, adjusted = self._ensure_fits_window(rows, cols, mines)
        if adjusted:
            self._set_field_vars(rows, cols, mines)
            messagebox.showinfo(
                "Размер поля",
                "Размеры скорректированы с учётом фактического размера окна:\n"
                f"{rows} строк × {cols} столбцов, {mines} мин.",
            )

    # --- Поле ---

    def _build_board(self) -> None:
        self.buttons.clear()
        for r in range(self.logic.rows):
            row_btns: list[tk.Button] = []
            for c in range(self.logic.cols):
                frame = tk.Frame(
                    self._board_frame,
                    width=self.layout.cell_px,
                    height=self.layout.cell_px,
                )
                frame.grid(row=r, column=c)
                frame.grid_propagate(False)

                btn = tk.Button(
                    frame,
                    font=self._font_cell,
                    padx=0,
                    pady=0,
                    borderwidth=1,
                    highlightthickness=0,
                    anchor="center",
                    justify="center",
                )
                btn.place(relx=0, rely=0, relwidth=1, relheight=1)
                btn.bind("<Button-1>", lambda _e, row=r, col=c: self._on_left_click(row, col))
                btn.bind("<Button-3>", lambda _e, row=r, col=c: self._on_right_click(row, col))
                row_btns.append(btn)
            self.buttons.append(row_btns)
        self._refresh_board()

    def _rebuild_board(self) -> None:
        for w in self._board_frame.winfo_children():
            w.destroy()
        self._build_board()

    def _refresh_board(self) -> None:
        if self.logic.is_game_over and not self.logic.is_won:
            self.logic.reveal_all_mines()
        for r in range(self.logic.rows):
            for c in range(self.logic.cols):
                if self._hint_cell != (r, c):
                    self._paint_button(r, c)

    def _paint_button(self, row: int, col: int) -> None:
        btn = self.buttons[row][col]
        cell = self.logic.board[row][col]

        if cell.is_open:
            btn.config(relief=tk.SUNKEN, state=tk.DISABLED)
            if cell.is_mine:
                btn.config(text=MINE_EMOJI, font=self._font_emoji, bg=MINE_BG, fg="black")
            elif not cell.neighbors:
                btn.config(text="", font=self._font_cell, bg=OPEN_BG, fg="black")
            else:
                btn.config(
                    text=str(cell.neighbors),
                    font=self._font_cell,
                    bg=OPEN_BG,
                    fg=NUMBER_COLORS[cell.neighbors],
                )
            return

        btn.config(
            relief=tk.RAISED,
            state=tk.NORMAL,
            bg="SystemButtonFace",
            fg="black",
            font=self._font_cell,
            text=FLAG_EMOJI if cell.is_flagged else "",
        )
        if cell.is_flagged:
            btn.config(font=self._font_emoji)

    # --- Таймер ---

    def _reset_timer(self) -> None:
        self._stop_timer()
        self._timer_seconds = 0
        self._timer_label.config(text="Время: 000 с")

    def _start_timer(self) -> None:
        if not self._timer_running:
            self._timer_running = True
            self._tick_timer()

    def _stop_timer(self) -> None:
        self._timer_running = False
        if self._timer_after_id:
            self.root.after_cancel(self._timer_after_id)
            self._timer_after_id = None

    def _tick_timer(self) -> None:
        if not self._timer_running:
            return
        self._timer_seconds += 1
        self._timer_label.config(text=f"Время: {self._timer_seconds:03d} с")
        self._timer_after_id = self.root.after(1000, self._tick_timer)

    # --- Подсказка ---

    def _clear_hint_highlight(self) -> None:
        if self._hint_after_id:
            self.root.after_cancel(self._hint_after_id)
            self._hint_after_id = None
        if self._hint_cell:
            row, col = self._hint_cell
            self._hint_cell = None
            self._paint_button(row, col)

    def _show_hint(self) -> None:
        if self.logic.is_game_over:
            return
        self._clear_hint_highlight()
        hint = self.logic.get_hint()
        if hint is None:
            messagebox.showinfo("Подсказка", "Сейчас нет гарантированной подсказки.")
            return

        kind, row, col = hint
        cell = self.logic.board[row][col]
        if cell.is_open or cell.is_flagged:
            messagebox.showinfo("Подсказка", "Сейчас нет гарантированной подсказки.")
            return

        self.buttons[row][col].config(
            bg=HINT_SAFE_BG if kind == "safe" else HINT_MINE_BG
        )
        self._hint_cell = (row, col)
        self._hint_after_id = self.root.after(HINT_HIGHLIGHT_MS, self._clear_hint_highlight)

    # --- События ---

    def _on_game_over(self) -> None:
        self._stop_timer()
        messagebox.showinfo("Сапёр", "Победа!" if self.logic.is_won else "Поражение!")

    def _on_left_click(self, row: int, col: int) -> None:
        if self.logic.is_game_over:
            return
        self._clear_hint_highlight()
        first_move = self.logic.is_first_move
        self.logic.open_cell(row, col)
        if first_move and not self.logic.is_first_move:
            self._start_timer()
        self._refresh_board()
        if self.logic.is_game_over:
            self._on_game_over()

    def _on_right_click(self, row: int, col: int) -> None:
        if self.logic.is_game_over:
            return
        self._clear_hint_highlight()
        self.logic.toggle_flag(row, col)
        self._paint_button(row, col)
