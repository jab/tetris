#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import curses
import itertools
import random
import threading
import time


# Define pieces by start position, relative to the top row and center col.
PIECES = (
    ("o", ((0, 0), (0, 1), (1, 1), (1, 0))),
    ("i", ((0, 0), (1, 0), (2, 0), (3, 0))),
    ("j", ((0, 0), (1, 0), (2, 0), (2, -1))),
    ("l", ((0, 0), (1, 0), (2, 0), (2, 1))),
    ("t", ((0, 0), (1, 0), (1, 1), (1, -1))),
    ("s", ((0, 1), (0, 0), (1, 0), (1, -1))),
    ("z", ((0, -1), (0, 0), (1, 0), (1, 1))),
)
LEFT = (0, -1)
RIGHT = (0, 1)
DOWN = (1, 0)


class Tetris:
    ADVANCE_DELAY = .5

    def __init__(self, redraw, nrows=20, ncols=10):
        self.redraw = redraw
        self.nrows = nrows
        self.ncols = ncols
        self.reset()
        threading.Thread(target=self.advance).start()

    def reset(self) -> None:
        self.board = [[None] * self.ncols for _ in range(self.nrows)]
        self.score = 0
        self.paused = False
        self.gameover = False
        self.quit = False
        self.next_piece()

    def _move_piece_to(self, pos) -> bool:
        if all(
            0 <= r < self.nrows and 0 <= c < self.ncols and not self.board[r][c]
            for (r, c) in pos
        ):
            self.piece_pos = pos
            return True
        return False

    def next_piece(self) -> None:
        self.piece_id, startpos = random.choice(PIECES)
        sr, sc = (0, self.ncols // 2)
        piece_pos = [(sr + r, sc + c) for (r, c) in startpos]
        if not self._move_piece_to(piece_pos):
            self.gameover = True

    def advance(self) -> None:
        while not self.quit:
            if self.paused or self.gameover:
                time.sleep(.02)
                continue
            time.sleep(self.ADVANCE_DELAY)
            if not self.move(DOWN):
                for (r, c) in self.piece_pos:
                    self.board[r][c] = self.piece_id
                self.handle_completed_rows()
                self.next_piece()
            self.redraw()

    def handle_completed_rows(self) -> None:
        check_rows = {r for (r, _) in self.piece_pos}
        completed = [r for r in check_rows if all(self.board[r])]
        if completed:
            self.redraw()
            time.sleep(self.ADVANCE_DELAY)
        for r in sorted(completed):
            self.board[1 : r + 1] = self.board[:r]
        n = len(completed)
        self.board[:n] = [[None] * self.ncols for _ in range(n)]

    def rotate(self, clockwise=True) -> bool:
        if self.piece_id == "o":
            return False
        cr, cc = self.piece_pos[1]  # center of rotation
        if clockwise:
            new_pos = [(cr - cc + c, cr + cc - r) for (r, c) in self.piece_pos]
        else:
            new_pos = [(cr + cc - c, cc - cr + r) for (r, c) in self.piece_pos]
        return self._move_piece_to(new_pos)

    def drop(self) -> None:
        while self.move(DOWN):
            pass

    def move(self, dir: "Literal[LEFT, RIGHT, DOWN]") -> bool:
        dr, dc = dir
        new_pos = [(r + dr, c + dc) for (r, c) in self.piece_pos]
        return self._move_piece_to(new_pos)


@curses.wrapper
def main(stdscr):
    def redraw():
        if t.quit:
            return
        stdscr.clear()
        s = ""
        for r in range(t.nrows):
            for c in range(t.ncols):
                if t.paused:
                    s += " - "
                elif t.board[r][c]:
                    s += f"[{t.board[r][c]}]"
                elif (r, c) in t.piece_pos:
                    s += "[ ]"
                else:
                    s += "   "
            s += "\n"
        stdscr.addstr(0, 0, s)
        spanned_cols = range(t.ncols) if t.paused else sorted(set(c for (r, c) in t.piece_pos))
        stdscr.addstr(r + 1, 0, "-"*3*spanned_cols[0] + "="*3*len(spanned_cols) + "-"*3*(t.ncols-spanned_cols[-1]-1))  # noqa: E501
        stdscr.addstr(r + 2, 0, f"Score: {t.score}")
        stdscr.addstr(r + 3, 0, t.gameover and "Game over!" or (t.paused and "Paused. P to unpause." or "Arrow keys (or HJKL) to move."))  # noqa: E501
        stdscr.addstr(r + 4, 0, "N for new game. Q to quit.")
        stdscr.refresh()

    t = Tetris(redraw)
    redraw()

    def getkey():
        try:
            return stdscr.getkey().lower()
        except KeyboardInterrupt:
            return "q"

    while (key := getkey()) != "q":
        should_redraw = True
        if key == "n":
            t.reset()
        elif key == "p":
            t.paused = not t.paused
        elif key in ("k", "key_up"):
            should_redraw = t.rotate(clockwise=True)
        elif key == "i":
            should_redraw = t.rotate(clockwise=False)
        elif key in ("h", "key_left"):
            should_redraw = t.move(LEFT)
        elif key in ("l", "key_right"):
            should_redraw = t.move(RIGHT)
        elif key in ("j", "key_down"):
            should_redraw = t.move(DOWN)
        elif key == " ":
            t.drop()
        if should_redraw:
            redraw()

    t.quit = True
