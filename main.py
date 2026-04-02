import tkinter as tk
from tkinter import messagebox
import random
import pandas as pd
import numpy as np
from ai_agent import get_best_move


class Analytics2048:
    def __init__(self, master):
        self.master = master
        self.master.title("Data-Driven 2048 (AI Enabled)")
        self.master.geometry("500x700")

        # Game State
        self.grid_size = 4
        self.board = np.zeros((4, 4), dtype=int)
        self.score = 0
        self.history = []
        self.time_limit = 30
        self.remaining_time = 30
        self.is_paused = False
        self.game_active = False

        self.setup_ui()
        self.trigger_pregame_countdown(3)

    # ---------------- UI ---------------- #
    def setup_ui(self):
        self.header = tk.Frame(self.master, bg="#bbada0", pady=10)
        self.header.pack(fill="x")

        self.lbl_timer = tk.Label(self.header, text="Ready?", font=("Verdana", 14), bg="#bbada0", fg="white")
        self.lbl_timer.pack(side="left", padx=20)

        self.lbl_score = tk.Label(self.header, text="Score: 0", font=("Verdana", 14, "bold"),
                                  bg="#bbada0", fg="white")
        self.lbl_score.pack(side="right", padx=20)

        self.game_container = tk.Frame(self.master, bg="#bbada0", bd=10)
        self.game_container.pack(pady=20)

        self.cells = []
        for r in range(4):
            row = []
            for c in range(4):
                cell = tk.Label(self.game_container, text="", width=5, height=2,
                                font=("Verdana", 22, "bold"),
                                bg="#cdc1b4", fg="#776e65")
                cell.grid(row=r, column=c, padx=5, pady=5)
                row.append(cell)
            self.cells.append(row)

        ctrl = tk.Frame(self.master)
        ctrl.pack(pady=10)

        tk.Button(ctrl, text="Pause/Resume", command=self.toggle_pause).pack(side="left", padx=5)
        tk.Button(ctrl, text="Reset", command=lambda: self.trigger_pregame_countdown(3)).pack(side="left", padx=5)

        # ✅ AI buttons
        tk.Button(ctrl, text="AI Move", command=self.ai_play).pack(side="left", padx=5)
        tk.Button(ctrl, text="Auto Play", command=self.auto_play).pack(side="left", padx=5)

    # ---------------- GAME START ---------------- #
    def trigger_pregame_countdown(self, sec):
        self.game_active = False
        if sec > 0:
            self.lbl_timer.config(text=f"Starting in {sec}...")
            self.master.after(1000, lambda: self.trigger_pregame_countdown(sec - 1))
        else:
            self.initialize_game()

    def initialize_game(self):
        self.board = np.zeros((4, 4), dtype=int)
        self.score = 0
        self.history = []
        self.remaining_time = self.time_limit
        self.game_active = True
        self.is_paused = False

        self.spawn_tile()
        self.spawn_tile()
        self.refresh_grid()
        self.run_timer()

        self.master.bind("<Key>", self.handle_keypress)

    # ---------------- CORE GAME ---------------- #
    def spawn_tile(self):
        empty = list(zip(*np.where(self.board == 0)))
        if empty:
            r, c = random.choice(empty)
            self.board[r, c] = 2 if random.random() < 0.9 else 4

    def refresh_grid(self):
        colors = {
            0: ("#cdc1b4", "#776e65"), 2: ("#eee4da", "#776e65"),
            4: ("#ede0c8", "#776e65"), 8: ("#f2b179", "white"),
            16: ("#f59563", "white"), 32: ("#f67c5f", "white"),
            64: ("#f65e3b", "white"), 128: ("#edcf72", "white"),
            256: ("#edcc61", "white"), 512: ("#edc850", "white"),
            1024: ("#edc53f", "white"), 2048: ("#edc22e", "white")
        }

        for r in range(4):
            for c in range(4):
                val = self.board[r, c]
                bg, fg = colors.get(val, ("#3c3a32", "white"))
                self.cells[r][c].config(text=str(val) if val else "", bg=bg, fg=fg)

        self.lbl_score.config(text=f"Score: {self.score}")

    def run_timer(self):
        if self.game_active and not self.is_paused:
            if self.remaining_time > 0:
                self.lbl_timer.config(text=f"Time: {self.remaining_time}s")
                self.remaining_time -= 1
                self.master.after(1000, self.run_timer)
            else:
                self.game_over("Time's Up!")

    # ---------------- MOVES ---------------- #
    def move_logic(self, board, direction):
        rotations = {"L": 0, "D": 1, "R": 2, "U": 3}
        temp = np.rot90(board, rotations[direction])

        new_board = []
        added_score = 0

        for row in temp:
            non_zero = row[row != 0]
            merged = []
            skip = False

            for i in range(len(non_zero)):
                if skip:
                    skip = False
                    continue

                if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
                    val = non_zero[i] * 2
                    merged.append(val)
                    added_score += val
                    skip = True
                else:
                    merged.append(non_zero[i])

            merged += [0] * (4 - len(merged))
            new_board.append(merged)

        final = np.rot90(np.array(new_board), -rotations[direction])
        return final, self.score + added_score

    # ---------------- INPUT ---------------- #
    def handle_keypress(self, event):
        if not self.game_active or self.is_paused:
            return

        key_map = {"Up": "U", "Down": "D", "Left": "L", "Right": "R"}
        if event.keysym not in key_map:
            return

        original = self.board.copy()
        self.board, self.score = self.move_logic(self.board, key_map[event.keysym])

        if not np.array_equal(original, self.board):
            self.log_data(event.keysym)
            self.spawn_tile()
            self.refresh_grid()

        if not self.can_move_exist():
            self.game_over("No moves left!")

    # ---------------- AI ---------------- #
    def game_logic(self, grid, move):
        mapping = {'LEFT': 'L', 'RIGHT': 'R', 'UP': 'U', 'DOWN': 'D'}
        new_board, new_score = self.move_logic(np.array(grid), mapping[move])
        moved = not np.array_equal(grid, new_board)
        return moved, new_score

    def ai_play(self):
        move = get_best_move(self.board.tolist(), self.game_logic)
        if move:
            self.board, self.score = self.move_logic(
                self.board,
                {'LEFT': 'L', 'RIGHT': 'R', 'UP': 'U', 'DOWN': 'D'}[move]
            )
            self.spawn_tile()
            self.refresh_grid()

    def auto_play(self):
        if not self.game_active or self.is_paused:
            return

        move = get_best_move(self.board.tolist(), self.game_logic)

        if move:
            self.board, self.score = self.move_logic(
                self.board,
                {'LEFT': 'L', 'RIGHT': 'R', 'UP': 'U', 'DOWN': 'D'}[move]
            )
            self.spawn_tile()
            self.refresh_grid()
            self.master.after(200, self.auto_play)

    # ---------------- DATA ---------------- #
    def log_data(self, key):
        self.history.append({
            "move": key,
            "score": self.score,
            "max_tile": int(np.max(self.board)),
            "empty_cells": int(np.count_nonzero(self.board == 0))
        })

    def can_move_exist(self):
        if 0 in self.board:
            return True
        for r in range(4):
            for c in range(4):
                if (c < 3 and self.board[r, c] == self.board[r, c + 1]) or \
                   (r < 3 and self.board[r, c] == self.board[r + 1, c]):
                    return True
        return False

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.run_timer()

    # ---------------- GAME OVER ---------------- #
    def game_over(self, reason):
        self.game_active = False
        self.master.unbind("<Key>")

        df = pd.DataFrame(self.history)
        print("\n--- Analytics ---")
        print(df.describe())

        messagebox.showinfo("Game Over", f"{reason}\nScore: {self.score}")


if __name__ == "__main__":
    root = tk.Tk()
    app = Analytics2048(root)
    root.mainloop()