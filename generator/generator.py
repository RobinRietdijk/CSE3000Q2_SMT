import numpy as np
import math
import argparse
import uuid
import os
import sys
from collections import deque
from asp import solve
from concurrent.futures import ProcessPoolExecutor, as_completed

# Change if you need a puzzle of n>31
# Might be dangerous
sys.setrecursionlimit(9970)

# Generates and saves the puzzle instance (relative to directory it is called from) if it passes basic validity checks
# Returns true if saved, and false if not
def generate(filename: str, n: int, seed: int = None, pcopyneighbour: int = -1, pcopyintersectionrowcolumn: int = -1, verbose: bool = False) -> bool:
    seed = np.random.SeedSequence(seed)
    seededRandomGenerator = np.random.default_rng(seed)

    found_solution = False

    for i in range(100):
        if found_solution:
            break
        solution = generateSolution(n, seededRandomGenerator)
        for j in range(5): # try to fill 5 times since generating is slow
            grid = create_puzzle_recursive(n, solution, seededRandomGenerator, pcopyneighbour, pcopyintersectionrowcolumn)
            # Grid generator was unable to make a valid puzzle
            if grid is None:
                if verbose:
                    print("Failed to generate valid puzzle")
                break

            # Basic validity checks
            # No more then [n/2] of the equal numbers in a row / column
            if not check_max_numbers(grid, n):
                if verbose:
                    print("Grid failed the max numbers check")
                continue
            # No more then 3 equal numbers following eachother
            if not check_max_consecutive_numbers(grid, n):
                if verbose:
                    print("Grid failed the max consecutive numbers check")
                continue

            # Run the solver for a solution and uniqueness check
            sol, unique = solve(grid)

            # Check solver output
            if not sol:
                if verbose:
                    print(f"Attempt #{i}:{j}: No valid solution found")
            elif not unique:
                if verbose:
                    print(f"Attempt #{i}:{j}: Not a unique solution")
            else:
                if verbose:
                    print(f"Attempt #{i}:{j}: Correct puzzle found!")
                found_solution = True
                break
     
    if not found_solution:
        return False

    if verbose:
        print ("Generated grid passed validity checks, saving...")
    # Make proper file structure for saving the puzzles
    folder = os.path.join("puzzles", f"{n}x{n}")
    os.makedirs(folder, exist_ok=True)
    full_path = os.path.join(folder, filename)

    with open(full_path, "w") as file:
        file.write(f"{n}\n\n")
        for row in grid:
            file.write(" ".join(map(str, row)) + "\n")
        file.write(f"\n@{seed.entropy}")
    
    return True

# Take every column and row and verify it has no more then [n/2] of the same number
def check_max_numbers(grid: np.ndarray, n: int) -> bool:
    maxOccurences = math.ceil(n / 2)
    if maxOccurences < 2:
        maxOccurences = 2

    # rows
    for row in grid:
        _, counts = np.unique(row, return_counts=True)
        if (np.any(counts > maxOccurences)):
            return False
        
    #columns
    for col in grid.T:
        _, counts = np.unique(col, return_counts=True)
        if (np.any(counts > maxOccurences)):
            return False
        
    return True

def check_max_consecutive_numbers(grid: np.ndarray, n: int) -> bool:
    #rows
    for row in grid:
        count = 1
        for i in range(1, len(row)):
            if (row[i] == row[i - 1]):
                count += 1
                if (count > 3):
                    return False
            else:
                count = 1

    #columns
    for col in grid.T:
        count = 1
        for i in range(1, len(col)):
            if (col[i] == col[i - 1]):
                count += 1
                if (count > 3):
                    return False
            else:
                count = 1
    
    return True

# Create a grid of 'black' cells, where a black cell is denoted as a '1'
def generateSolution(n, generator):
    pattern = np.zeros((n, n))  

    # Create a randomly shuffled list of all cells
    cells = [(r, c) for r in range(n) for c in range(n)]
    generator.shuffle(cells)

    flipped = 0
    for r, c, in cells:

        # Check surrounding squares
        hasBlackNeighbour = any(0 <= rr < n and 0 <= cc < n and pattern[rr, cc] == 1
                                 for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)))
        if hasBlackNeighbour:
            continue

        pattern[r, c] = 1
        
        d_black_neighbours = 0
        walls = 0
        for rr, cc in ((r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)):
            if 0 <= rr < n and 0 <= cc < n:
                if pattern[rr, cc] == 1:
                    d_black_neighbours += 1
            else:
                # We dont care about inrementing walls, since we can only be next to 1 wall. 
                # If we are next to 2 walls we are in a corner and the white area cannot be split here
                walls = 1

        # We cannot split the white area if there is only one or no diagonal connection with a black square    
        if d_black_neighbours + walls < 2:
            flipped += 1
            continue 

        neighbours = [(rr, cc) for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))if 0 <= rr < n and 0 <= cc < n]
        start = neighbours[0] 
        goals = set(neighbours[1:])
        # We check if we can reach each neighbour from each other
        # (note that this property is transitive, so we can pick one and search from there)
        # If this is the case, every white square is still connected
        if bfs_white(start, goals, pattern, n):
            flipped += 1
        else:
            pattern[r, c] = 0
            
    return pattern

# Use breadth first search to attempt to visit all squares listed in 'to'
def bfs_white(start, to, pattern, n) -> bool:
    visited = set()
    queue = deque()
    queue.append(start)
    visited.add(start)
    while queue:
        r, c = queue.popleft()
        if (r, c) in to:
            to.remove((r, c))
            if len(to) == 0:
                return True

        for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if 0 <= rr < n and 0 <= cc < n and pattern[rr, cc] == 0 and (not (rr, cc) in visited):
                queue.append((rr, cc))
                visited.add((rr,cc))

    return False

# Generate a puzzle using recursive backtracking
def create_puzzle_recursive(n, solution, generator, pcopyneighbour, pcopyintersectionrowcolumn):
    grid = np.zeros((n, n), dtype=int)

    white_cells = [(r, c) for r in range(n) for c in range(n) if solution[r, c] == 0]
    black_cells = [(r, c) for r in range(n) for c in range(n) if solution[r, c] == 1]

    used_in_row = [set() for _ in range(n)]
    used_in_col = [set() for _ in range(n)]

    # Returns True if a solution is found
    # false if not. Number specifies amount of steps to backtrack
    def backtracking(id):
        if id == len(white_cells):
            return (True, None)
        
        r, c = white_cells[id]

        # Find all possible values for this cell
        forbidden = used_in_row[r] | used_in_col[c]
        candidates = [i for i in range(1, n+1) if i not in forbidden]
        if not candidates:
            # conflict has arised
            # this must be because all numbers are already used up in row and column
            # we backtrack till we find the first number in the row that doesn't appear in that column
            # we undo that assignment and then try again
            # let's analyze where the conflict happens
            num_backtracks = 1
            while True:
                c2 = c - num_backtracks
                if c2 < 0:
                    print("A conflict arised but conflict analysis failed (which shouldn't happen?). Aborting generation")
                    exit(1)

                if not grid[r, c2] in used_in_col[c]:
                    # conflict cause found
                    return (False, num_backtracks)

                num_backtracks += 1
        
        # Shuffle candidates and attempt to assign
        generator.shuffle(candidates)

        for i in candidates:
            grid[r, c] = i
            used_in_row[r].add(i)
            used_in_col[c].add(i)
            (success, num_backtracks) = backtracking(id+1)
            if success:
                return (True, None)
            used_in_row[r].remove(i)
            used_in_col[c].remove(i)
            grid[r, c] = 0
            num_backtracks = num_backtracks - 1
            if num_backtracks > 0:
                return (False, num_backtracks)
        return (False, 1)
    
    # Start filling algorithm with backtracking
    # if False, it could not generate a valid solution
    if not backtracking(0)[0]:
        return None
    
    # Generate numbers for black squares
    for r, c in black_cells:

        if pcopyneighbour != -1 or pcopyintersectionrowcolumn != -1:

            p = generator.random()

            # optimize by randomly picking the number of a neighbour or row/col intersection
            if p < pcopyneighbour:
                neighbours = [grid[rr, cc] for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))if 0 <= rr < n and 0 <= cc < n]
                grid[r, c] = generator.choice(neighbours)

                continue
            elif p - max(0, pcopyneighbour) < pcopyintersectionrowcolumn:
                used = list(used_in_row[r].union(used_in_col[c]))
                if len(used) > 0:
                    grid[r, c] = generator.choice(used)
                    continue


        # Only choose numbers that occur in row and/or column
        # since otherwise the black cell could also be white
        # which means there are multiple solutions
        used = list(used_in_row[r].union(used_in_col[c]))
        grid[r, c] = generator.choice(used) 
    return grid

# Helper function for parallelization
def _generate_one(filename, n, seed, pcopyneighbour, pcopyintersectionrowcolumn):
    success = False
    while not success:
        success = generate(filename, n, seed, pcopyneighbour, pcopyintersectionrowcolumn)
    return filename

# Run the generator from command line, using the arguments if needed
# Example: generate 3 4x4 puzzle instances, and save to the folder 'newGenerations' (Make sure the folder exists)
# python generator.py -c 3 -n 4 -f newGenerations/
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate n x n singles puzzle(s)")

    # Optional filename prefix
    parser.add_argument(
        "-f", "--filename",
        type=str,
        default=None,
        help="Prefix for the generated puzzle file(s)"
    )

    # Optional count
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=1,
        help="Number of puzzles to generate"
    )

    # Optional seed (will generate equal puzzles if count > 1)
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        help="Seed for number generation (will create all equal puzzles if count > 1)"
    )

    # Required n x n size
    parser.add_argument(
        "-n", '--size',
        type=int,
        required=True,
        help="Size of the puzzle (n x n)"
    )

    parser.add_argument(
        "-pn", "--pcopyneighbour",
        type=float,
        default=-1,
        help="Chance the number of a black square is that of a neighbour instead of random"
    )

    parser.add_argument(
        "-pi", "--pcopyintersectionrowcolumn",
        type=float,
        default=-1,
        help="Chance the number of a black square is that of intersection of row and column instead of random"
    )

    args = parser.parse_args()
    
    # Prepare list of filenames
    filenames = []
    for i in range(args.count):
        uid = uuid.uuid4()
        if args.filename:
            filename = f"{args.filename}{uid}.singles"
        else:
            filename = f"{uid}.singles"
        filenames.append(filename)

    max_workers = os.cpu_count() or 1

    # Setup worker pool
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_generate_one, filename, args.size, args.seed, args.pcopyneighbour, args.pcopyintersectionrowcolumn) 
            for filename in filenames
        ]
        
        id = 0
        for future in as_completed(futures):
            id += 1
            generated_file = future.result()
            print(f"Generated puzzle {id}: {generated_file}")

        executor.shutdown()
