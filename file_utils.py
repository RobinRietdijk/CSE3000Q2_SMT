import os
import sys

VALID_EXTENSIONS = [".singles"]

def _is_puzzle(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in VALID_EXTENSIONS

def _read_puzzle(path: str) -> list:
    with open(path, "r") as f:
        lines = f.readlines()

    try:
        n = int(lines[0])
    except (ValueError, IndexError):
        sys.exit(f"Error: First line must contain puzzle size in {path}")

    if len(lines) < n + 2:
        sys.exit(f"Error: Wrong puzzle format in {path}")

    grid = []
    for i in range(2, n + 2):
        row_values = lines[i].split()

        if len(row_values) != n:
            sys.exit(f"Error: Row length mismatch in {path}")
            
        try:
            row = [int(x) for x in row_values]
        except ValueError:
            sys.exit(f"Error: Non-integer value in {path}")

        grid.append(row)
    
    seed = lines[n+3]
    return grid, seed

def read_file(path: str) -> list:
    if not os.path.exists(path):
        sys.exit(f"Error: File does not exist at {path}")
    if not _is_puzzle(path):
        sys.exit(f"Error: Not a puzzle file at {path}")

    puzzle, seed = _read_puzzle(path)
    fname = os.path.splitext(os.path.basename(path))[0]
    return [(fname, puzzle, seed)]

def read_folder(path: str) -> list:
    if not os.path.isdir(path):
        sys.exit(f"Error: Not a directory at {path}")

    puzzles = []
    for filename in os.listdir(path):
        file = os.path.join(path, filename)

        # Filter out subfolders
        if not os.path.isfile(file):
            continue

        puzzles.extend(read_file(file))
    if not puzzles:
        sys.exit(f"Error: No puzzle files found in {path}")
    return puzzles