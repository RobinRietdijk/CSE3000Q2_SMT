import os
import sys

PUZZLE_EXTENSIONS = [".singles"]
SOLUTION_EXTENSIONS = [".singlessol"]

def _is_puzzle(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in PUZZLE_EXTENSIONS

def _is_solution(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in SOLUTION_EXTENSIONS

def _parse_file(path: str) -> tuple[list[list[int|str]], str|None]:
    _, ext = os.path.splitext(path)
    with open(path, "r") as f:
        lines = f.readlines()

    try:
        n = int(lines[0])
    except (ValueError, IndexError):
        sys.exit(f"Error: First line must contain size in {path}")

    if len(lines) < n + 2:
        sys.exit(f"Error: Wrong format in {path}")

    grid = []
    for i in range(2, n + 2):
        row_values = lines[i].split()

        if len(row_values) != n:
            sys.exit(f"Error: Row length mismatch in {path}")
            
        try:
            if ext.lower() in SOLUTION_EXTENSIONS:
                row = row_values
            else:
                row = [int(x) for x in row_values]
        except ValueError:
            sys.exit(f"Error: Unknown value type in {path}")

        grid.append(row)
    
    seed = None
    if len(lines) > n+3:
        line = lines[n+3].strip()
        if line.startswith("@"):
            seed = line[1:]
        else:
            print(f"Warning: seed not prepended with @ in {path}")
    
    return grid, seed

def _read_file(path: str, puzzles: bool, strict: bool) -> list[tuple[str, list[list[int|str]], str|None]]:
    if not os.path.exists(path):
        sys.exit(f"Error: File does not exist at {path}")
    if (puzzles and not _is_puzzle(path)) or (not puzzles and not _is_solution(path)):
        if strict:
            sys.exit(f"Error: Not a {'puzzle' if puzzles else 'solution'} file at {path}")
        else:
            print(f"Warning: Not a {'puzzle' if puzzles else 'solution'} file at {path}")
            return []

    grid, seed = _parse_file(path)
    fname = os.path.splitext(os.path.basename(path))[0]
    return [(fname, grid, seed)]

def _read_dir(path: str, puzzles: bool, strict: bool) -> list[tuple[str, list[list[int|str]], str|None]]:
    if not os.path.isdir(path):
        sys.exit(f"Error: Not a directory at {path}")

    grids = []
    for filename in os.listdir(path):
        file = os.path.join(path, filename)

        # Filter out subfolders
        if not os.path.isfile(file):
            continue

        grids.extend(_read_file(file, puzzles, strict))
    if not grids:
        sys.exit(f"Error: No {'puzzle' if puzzles else 'solution'} files found in {path}")
    return grids

def read_puzzle(path: str, strict: bool = False) -> tuple[str, list[list[int|str]], str]:
    result = _read_file(path, True, strict)
    if not result:
        sys.exit(f"Error: No puzzle file found at {path}")
    return result[0]

def read_solution(path: str, strict: bool = False) -> tuple[str, list[list[int|str]], str]:
    result = _read_file(path, False, strict)
    if not result:
        sys.exit(f"Error: No solution file found at {path}")
    return result[0]

def read_puzzle_dir(path: str, strict: bool = False) -> list[tuple[str, list[list[int|str]], str|None]]:
    return _read_dir(path, True, strict)

def read_solution_dir(path: str, strict: bool = False) -> list[tuple[str, list[list[int|str]], str|None]]:
    return _read_dir(path, False, strict)

def write_file(fname: str, puzzle: list[list[int|str]], seed: str|None) -> None:
    os.makedirs("solutions", exist_ok=True)
    fname += ".singlessol"
    path = os.path.join("solutions", fname)

    with open(path, "w") as file:
        file.write(f"{len(puzzle)}\n\n")
        for row in puzzle:
            file.write(" ".join(map(str, row)) + "\n")
        if seed is not None:
            file.write(f"\n@{seed}")