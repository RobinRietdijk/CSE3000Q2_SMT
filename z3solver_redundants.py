from z3 import *

# Redundant constraint to make sure evert white cell has atleast one white neighbour
def white_neighbours(s: Solver, colored: list[list[BoolRef]], n: int) -> None:
    for i in range(n):
        for j in range(n):
            neighbours = []
            if i > 0:
                neighbours.append(Not(colored[i-1][j]))
            if j > 0:
                neighbours.append(Not(colored[i][j-1]))
            if i+1 < n:
                neighbours.append(Not(colored[i+1][j]))
            if j+1 < n:
                neighbours.append(Not(colored[i][j+1]))
            
            if neighbours:
                s.add(Implies(Not(colored[i][j]), Or(*neighbours)))

# Redundant constraint to make sure there is at least one white in each row and column
def atleast_one_white(s: Solver, colored: list[list[BoolRef]], n: int) -> None:
    for i in range(n):
        rows = []
        cols = []
        for j in range(n):
            rows.append(Not(colored[i][j]))
            cols.append(Not(colored[j][i]))
        s.add(Or(*rows))
        s.add(Or(*cols))

# Redundant constraint for corners
def corners_implications(s: Solver, colored: list[list[BoolRef]], n: int) -> None:
    s.add(Implies(colored[0][1], Not(colored[1][0])))
    s.add(Implies(colored[1][0], Not(colored[0][1])))
    s.add(Implies(colored[0][n-2], Not(colored[1][n-1])))
    s.add(Implies(colored[1][n-1], Not(colored[0][n-2])))
    s.add(Implies(colored[n-2][0], Not(colored[n-1][1])))
    s.add(Implies(colored[n-1][1], Not(colored[n-2][0])))
    s.add(Implies(colored[n-1][n-2], Not(colored[n-2][n-1])))
    s.add(Implies(colored[n-2][n-1], Not(colored[n-1][n-2])))