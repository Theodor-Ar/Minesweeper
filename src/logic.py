"""Логика игры."""

import random
from typing import Any


class MinesweeperLogic:
    """Состояние поля и правила."""

    def __init__(self, rows: int, cols: int, mines: int) -> None:
        self.rows = rows
        self.cols = cols
        self.mines = mines

        self.is_first_move = True
        self.is_game_over = False
        self.is_won = False

        self._init_board()

    def _init_board(self) -> None:
        """Пустое поле без мин — мины появятся только после первого хода."""
        self.board: list[list[dict[str, Any]]] = [
            [
                {
                    "is_mine": False,
                    "is_open": False,
                    "is_flagged": False,
                    "neighbors": 0,
                }
                for _ in range(self.cols)
            ]
            for _ in range(self.rows)
        ]

    def reset(self) -> None:
        """Сбросить поле для новой партии."""
        self.is_first_move = True
        self.is_game_over = False
        self.is_won = False
        self._init_board()

    def _safe_zone(self, safe_row: int, safe_col: int) -> set[tuple[int, int]]:
        """Клетки 3×3 вокруг первого клика — зона без мин."""
        zone: set[tuple[int, int]] = set()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                r, c = safe_row + dr, safe_col + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    zone.add((r, c))
        return zone

    def _place_mines(self, safe_row: int, safe_col: int) -> None:
        """Расставить мины после первого хода. Безопасная зона 3×3 исключена."""
        forbidden = self._safe_zone(safe_row, safe_col)
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in forbidden
        ]
        count = min(self.mines, len(candidates))
        for r, c in random.sample(candidates, count):
            self.board[r][c]["is_mine"] = True

    def _calculate_numbers(self) -> None:
        """Посчитать количество мин-соседей для каждой клетки."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c]["is_mine"]:
                    continue
                neighbors = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.board[nr][nc]["is_mine"]:
                                neighbors += 1
                self.board[r][c]["neighbors"] = neighbors

    def _reveal_cell(self, row: int, col: int) -> None:
        cell = self.board[row][col]
        if cell["is_open"] or cell["is_flagged"] or cell["is_mine"]:
            return

        cell["is_open"] = True
        if cell["neighbors"] == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self._reveal_cell(nr, nc)

    def open_cell(self, row: int, col: int) -> None:
        """Открыть клетку. На первом ходу — мины, числа, затем открытие."""
        if self.is_game_over:
            return

        cell = self.board[row][col]
        if cell["is_open"] or cell["is_flagged"]:
            return

        if self.is_first_move:
            self._place_mines(safe_row=row, safe_col=col)
            self._calculate_numbers()
            self.is_first_move = False
            # После расстановки: первая клетка и её 3×3 без мин → neighbors == 0.

        if cell["is_mine"]:
            cell["is_open"] = True
            self.is_game_over = True
            self.is_won = False
            return

        self._reveal_cell(row, col)

        if self.check_win_condition():
            self.is_game_over = True
            self.is_won = True

    def toggle_flag(self, row: int, col: int) -> None:
        """Поставить/снять флаг."""
        if self.is_game_over:
            return

        cell = self.board[row][col]
        if cell["is_open"]:
            return

        cell["is_flagged"] = not cell["is_flagged"]

    def check_win_condition(self) -> bool:
        """True, если все не-минные клетки открыты."""
        for row in self.board:
            for cell in row:
                if not cell["is_mine"] and not cell["is_open"]:
                    return False
        return True

    def reveal_all_mines(self) -> None:
        """Показать все мины (при поражении)."""
        for row in self.board:
            for cell in row:
                if cell["is_mine"]:
                    cell["is_open"] = True
