import argparse
import os
import z3solver
from file_utils import read_file, read_folder

def write_file(fname: str, puzzle: list, seed: str) -> None:
    os.makedirs("solutions", exist_ok=True)
    fname += ".singlessol"
    path = os.path.join("solutions", fname)

    with open(path, "w") as file:
        file.write(f"{len(puzzle)}\n\n")
        for row in puzzle:
            file.write(" ".join(map(str, row)) + "\n")
        file.write(f"\n{seed}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hitori solver using Z3")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", type=str, help="Path to a puzzle file")
    group.add_argument("-d", "--folder", type=str, help="Path to folder containing puzzle files")
    args = parser.parse_args()

    if args.file:
        puzzles = read_file(args.file)
    else:
        puzzles = read_folder(args.folder)

    for name, puzzle, seed in puzzles:
        print(f"Solving {name}")
        solution = z3solver.solve(puzzle)
        write_file(name, solution, seed)
