from z3 import *

# Distinct tactic following Z3py basics, SMT/SAT describes a one-hot approach for latin squares
def constraint_uniquecells(s: Solver, colored: list, grid: list, n: int) -> None:
    for i in range(n):
        for j in range(n):
            for k in range(j+1, n):
                # If 2 cells have an equal symbol, we must color one black
                if (grid[i][j] == grid[i][k]):
                    s.add(Or(colored[i][j], colored[i][k]))
                    
    for i in range(n):
        for j in range(n):
            for k in range(j+1, n):
                if (grid[j][i] == grid[k][i]):
                    s.add(Or(colored[j][i], colored[k][i]))

# Trivial, remove i-1 and j-1, since we already check those in earlier cells
def constraint_neighbours(s: Solver, colored: list, n: int) -> None:
    for i in range(n):
        for j in range(n):
            if i+1 < n:
                # Horizontal neighbours
                s.add(Not(And(colored[i][j], colored[i+1][j])))
            if j+1 < n:
                # Vertical neighbours
                s.add(Not(And(colored[i][j], colored[i][j+1])))

def constraint_connectedwhite(s: Solver, colored: list, grid: list, n: int) -> None:
    return

def solve(puzzle: list) -> None:
    n = len(puzzle)
    s = Solver()
    colored = [[Bool(f"B_{i},{j}") for j in range(n)] for i in range(n)]
    constraint_uniquecells(s, colored, puzzle, n)
    constraint_neighbours