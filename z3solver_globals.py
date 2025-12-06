from z3 import *

# Redundant constraint to make sure there is at least n / 2 in each row and column
def atleast_whites(s: Solver, colored: list[list[BoolRef]], n: int) -> None:
    min_white = n//2
    for i in range(n):
        s.add(AtLeast(*[Not(colored[i][j]) for j in range(n)], min_white))
        s.add(AtLeast(*[Not(colored[j][i]) for j in range(n)], min_white))

# Redundant constraint to make sure there is at most (n / 2) + 1 blacks in each row and column
def atmost_blacks(s: Solver, colored: list[list[BoolRef]], n: int) -> None:
    max_black = (n//2)+1
    for i in range(n):
        s.add(AtMost(*[colored[i][j] for j in range(n)], max_black))
        s.add(AtMost(*[colored[j][i] for j in range(n)], max_black))

# Redundant constraint for pairs, making all other occurences of those values black
def pair_isolation(s: Solver, colored: list[list[BoolRef]], grid: list[list[int]], n: int) -> None:
    if n < 4:
        return
    
    for i in range(n):
        for j in range(n-1):
            if grid[i][j] == grid[i][j+1]:
                for k in range(n):
                    if k not in (j-1, j, j+1, j+2) and grid[i][j] == grid[i][k]:
                        s.add(colored[i][k])
            
            if grid[j][i] == grid[j+1][i]:
                for k in range(n):
                    if k not in (j-1, j, j+1, j+2) and grid[j][i] == grid[k][i]:
                        s.add(colored[k][i])

# Implementation of pattern 6 according to chapter 3.3 of Hitori Solver
def gh_pattern_6(s: Solver, colored: list[list[BoolRef]], grid: list[list[int]], n: int) -> None:
    for i in range(n):
        for j in range(n-1):
            if grid[i][j] == grid[i][j+1]:
                for k in range(n):
                    if k not in (j, j+1) and grid[i][k] == grid[i][j]:
                        s.add(colored[i][k])

            
            if grid[j][i] == grid[j+1][i]:
                for k in range(n):
                    if k not in (j, j+1) and grid[k][i] == grid[j][i]:
                        s.add(colored[k][i])

# Implementation of pattern 7 according to chapter 3.3 of Hitori Solver
def gh_pattern_7(s: Solver, colored: list[list[BoolRef]], grid: list[list[int]], n: int) -> None:
    for i in range(n):
        for j in range(n-2):
            if grid[i][j] == grid[i][j+2]:
                conditions = []
                if i > 0:
                    conditions.append(colored[i-1][j+1])
                if i < n-1:
                    conditions.append(colored[i+1][j+1])
                
                if not conditions:
                    continue
                condition = And(*conditions) if len(conditions) > 1 else conditions[0]

                for k in range(n):
                    if k not in (j, j+2) and grid[i][k] == grid[i][j]:
                        s.add(Implies(condition, colored[i][k]))

    for j in range(n):
        for i in range(n-2):
            if grid[i][j] == grid[i+2][j]:
                conditions = []
                if j > 0:
                    conditions.append(colored[i+1][j-1])
                if j < n-1:
                    conditions.append(colored[i+1][j+1])
                
                if not conditions:
                    continue
                condition = And(*conditions) if len(conditions) > 1 else conditions[0]

                for k in range(n):
                    if k not in (i, i+2) and grid[k][j] == grid[i][j]:
                        s.add(Implies(condition, colored[k][j]))

# Implementation of pattern 8 according to chapter 3.3 of Hitori Solver
def gh_pattern_8(s: Solver, colored: list[list[BoolRef]], grid: list[list[int]], n: int) -> None:
    for i in range(n):
        if grid[0][i] == grid[1][i]:
            if i > 1:
                if grid[0][i] == grid[1][i-1]:
                    s.add(Implies(colored[0][i-2], colored[1][i]))
            if i < n-2:
                if grid[0][i] == grid[1][i+1]:
                    s.add(Implies(colored[0][i+2], colored[1][i]))
         
        if grid[n-1][i] == grid[n-2][i]:
            if i > 1:
                if grid[n-1][i] == grid[n-2][i-1]:
                    s.add(Implies(colored[n-1][i-2], colored[n-2][i]))
            if i < n-2:
                if grid[n-1][i] == grid[n-2][i+1]:
                    s.add(Implies(colored[n-1][i+2], colored[n-2][i]))
        
        if grid[i][0] == grid[i][1]:
            if i > 1:
                if grid[i][0] == grid[i-1][1]:
                    s.add(Implies(colored[i-2][0], colored[i][1]))
            if i < n-2:
                if grid[i][0] == grid[i+1][1]:
                    s.add(Implies(colored[i+2][0], colored[i][1]))
        
        if grid[i][n-1] == grid[i][n-2]:
            if i > 1:
                if grid[i][n-1] == grid[i-1][n-2]:
                    s.add(Implies(colored[i-2][n-1], colored[i][n-2]))
            if i < n-2:
                if grid[i][n-1] == grid[i+1][n-2]:
                    s.add(Implies(colored[i+2][n-1], colored[i][n-2]))

def bridges(s: Solver, colored: list[list[BoolRef]], n: int) -> None:
    for i in range(n-1):
        whites_in_row1 = Or(*[Not(colored[i][j]) for j in range(n)])
        whites_in_row2 = Or(*[Not(colored[i+1][j]) for j in range(n)])

        row_bridge = Or(*[And(Not(colored[i][j]), Not(colored[i+1][j])) for j in range(  n)])
        s.add(Implies(And(whites_in_row1, whites_in_row2), row_bridge))

        whites_in_col1 = Or(*[Not(colored[j][i]) for j in range(n)])
        whites_in_col2 = Or(*[Not(colored[j][i+1]) for j in range(n)])

        col_bridge = Or(*[And(Not(colored[j][i]), Not(colored[j][i+1])) for j in range(n)])
        s.add(Implies(And(whites_in_col1, whites_in_col2), col_bridge))