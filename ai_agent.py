import random
import copy

MOVES = ['UP', 'DOWN', 'LEFT', 'RIGHT']

def evaluate(grid):
    empty = sum(row.count(0) for row in grid)
    max_tile = max(max(row) for row in grid)
    return empty * 100 + max_tile

def simulate_move(grid, move, game_logic):
    new_grid = copy.deepcopy(grid)
    moved, score = game_logic(new_grid, move)
    return new_grid if moved else None

def expectimax(grid, depth, is_max, game_logic):
    if depth == 0:
        return evaluate(grid)

    if is_max:
        best = -float('inf')
        for move in MOVES:
            new_grid = simulate_move(grid, move, game_logic)
            if new_grid:
                val = expectimax(new_grid, depth - 1, False, game_logic)
                best = max(best, val)
        return best

    else:
        empty_cells = [(i, j) for i in range(4) for j in range(4) if grid[i][j] == 0]
        if not empty_cells:
            return evaluate(grid)

        total = 0
        for i, j in empty_cells:
            for value, prob in [(2, 0.9), (4, 0.1)]:
                new_grid = copy.deepcopy(grid)
                new_grid[i][j] = value
                total += prob * expectimax(new_grid, depth - 1, True, game_logic)

        return total / len(empty_cells)

def get_best_move(grid, game_logic, depth=3):
    best_move = None
    best_value = -float('inf')

    for move in MOVES:
        new_grid = simulate_move(grid, move, game_logic)
        if new_grid:
            value = expectimax(new_grid, depth, False, game_logic)
            if value > best_value:
                best_value = value
                best_move = move

    return best_move