"""Логика игры."""

import random
from dataclasses import dataclass
from typing import Iterator, Literal
from src.config import (
    MIN_ROWS,
    MIN_COLS,
    MIN_FREE_CELLS,
    STANDARD_ROWS,
    STANDARD_COLS,
    STANDARD_MINES,
    NEIGHBOR_OFFSETS
)

HintKind = Literal["safe", "mine"]
HintResult = tuple[HintKind, int, int] | None


@dataclass
class Cell:
    is_mine: bool = False
    is_open: bool = False
    is_flagged: bool = False
    neighbors: int = 0


class MinesweeperLogic:
    """Состояние поля и правила."""

    def __init__(self, rows: int, cols: int, mines: int) -> None:
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.is_first_move = True
        self.is_game_over = False
        self.is_won = False
        self.board: list[list[Cell]] = []
        self._init_board()

    @staticmethod
    def validate_settings(rows: int, cols: int, mines: int) -> tuple[bool, str]:
        if rows < MIN_ROWS:
            return False, f"Строк должно быть не меньше {MIN_ROWS}."
        if cols < MIN_COLS:
            return False, f"Столбцов должно быть не меньше {MIN_COLS}."
        if mines <= 0:
            return False, "Количество мин должно быть больше 0."

        total = rows * cols
        max_mines = total - MIN_FREE_CELLS
        if mines > max_mines:
            return (
                False,
                f"Слишком много мин. Максимум для поля {rows}x{cols}: {max_mines}.",
            )
        return True, ""

    @staticmethod
    def clamp_mines(rows: int, cols: int, mines: int) -> int:
        return min(mines, max(1, rows * cols - MIN_FREE_CELLS))

    def new_game(self, rows: int, cols: int, mines: int) -> None:
        self.rows, self.cols, self.mines = rows, cols, mines
        self.reset()

    def reset(self) -> None:
        self.is_first_move = True
        self.is_game_over = False
        self.is_won = False
        self._init_board()

    def _init_board(self) -> None:
        self.board = [
            [Cell() for _ in range(self.cols)] for _ in range(self.rows)
        ]

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def _neighbors(self, row: int, col: int) -> Iterator[tuple[int, int]]:
        for dr, dc in NEIGHBOR_OFFSETS:
            r, c = row + dr, col + dc
            if self._in_bounds(r, c):
                yield r, c

    def _safe_zone(self, safe_row: int, safe_col: int) -> set[tuple[int, int]]:
        return {
            (safe_row + dr, safe_col + dc)
            for dr, dc in NEIGHBOR_OFFSETS
            if self._in_bounds(safe_row + dr, safe_col + dc)
        } | {(safe_row, safe_col)}

    def _place_mines(self, safe_row: int, safe_col: int) -> None:
        forbidden = self._safe_zone(safe_row, safe_col)
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in forbidden
        ]
        for r, c in random.sample(candidates, min(self.mines, len(candidates))):
            self.board[r][c].is_mine = True

    def _calculate_numbers(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if cell.is_mine:
                    continue
                cell.neighbors = sum(
                    1
                    for nr, nc in self._neighbors(r, c)
                    if self.board[nr][nc].is_mine
                )

    def _reveal_cell(self, row: int, col: int) -> None:
        cell = self.board[row][col]
        if cell.is_open or cell.is_flagged or cell.is_mine:
            return
        cell.is_open = True
        if cell.neighbors == 0:
            for nr, nc in self._neighbors(row, col):
                self._reveal_cell(nr, nc)

    def open_cell(self, row: int, col: int) -> None:
        if self.is_game_over:
            return

        cell = self.board[row][col]
        if cell.is_open or cell.is_flagged:
            return

        if self.is_first_move:
            self._place_mines(row, col)
            self._calculate_numbers()
            self.is_first_move = False

        if cell.is_mine:
            cell.is_open = True
            self.is_game_over = True
            self.is_won = False
            return

        self._reveal_cell(row, col)
        if self.check_win_condition():
            self.is_game_over = True
            self.is_won = True

    def toggle_flag(self, row: int, col: int) -> None:
        if self.is_game_over:
            return
        cell = self.board[row][col]
        if not cell.is_open:
            cell.is_flagged = not cell.is_flagged

    def check_win_condition(self) -> bool:
        return all(
            cell.is_open or cell.is_mine
            for row in self.board
            for cell in row
        )

    def reveal_all_mines(self) -> None:
        for row in self.board:
            for cell in row:
                if cell.is_mine:
                    cell.is_open = True

    def _neighbor_closures(self, row: int, col: int) -> tuple[list[tuple[int, int]], int]:
        closed: list[tuple[int, int]] = []
        flags = 0
        for nr, nc in self._neighbors(row, col):
            neighbor = self.board[nr][nc]
            if neighbor.is_open:
                continue
            if neighbor.is_flagged:
                flags += 1
            else:
                closed.append((nr, nc))
        return closed, flags

    def get_hint(self) -> HintResult:
        safe_cells: list[tuple[int, int]] = []
        mine_cells: list[tuple[int, int]] = []

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if not cell.is_open or not cell.neighbors:
                    continue

                closed, flags = self._neighbor_closures(r, c)
                if cell.neighbors == flags:
                    safe_cells.extend(closed)
                elif cell.neighbors == flags + len(closed):
                    mine_cells.extend(closed)

        if safe_cells:
            return "safe", safe_cells[0][0], safe_cells[0][1]
        if mine_cells:
            return "mine", mine_cells[0][0], mine_cells[0][1]
        return None
