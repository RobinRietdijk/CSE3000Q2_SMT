import argparse
import time
import os
import z3solver
from datetime import datetime
from file_utils import read_puzzle, read_puzzle_dir, read_solution, read_solution_dir, write_file, append_comment
from checker import check_puzzle

def _format_elapsed(elapsed: float) -> str:
    if elapsed < 1.0:
        ms = elapsed*1000
        return f"{ms:.3f} ms"
    else:
        return f"{elapsed:.6f} s"

def _check_command(args):
    if args.file:
        solutions = [read_solution(args.file)]
    else:
        solutions = read_solution_dir(args.folder)

    for path, solution, _ in solutions:
        fname = os.path.splitext(os.path.basename(path))[0]

        correct = check_puzzle(solution)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if correct:
            print(f"{fname}: Correct solution")
            append_comment(path, f"Solution checked to be CORRECT on {timestamp}")
        else:
            print(f"{fname}: Incorrect solution")
            append_comment(path, f"Solution checked to be INCORRECT on {timestamp}")

def _solve_command(args):
    if args.file:
        puzzles = [read_puzzle(args.file)]
    else:
        puzzles = read_puzzle_dir(args.folder)

    os.makedirs("solutions", exist_ok=True)
    for path, puzzle, seed in puzzles:
        fname = os.path.splitext(os.path.basename(path))[0]
        start = time.perf_counter()
        solution = z3solver.solve(puzzle)
        end = time.perf_counter()
        elapsed = end-start
        
        print(f"Solved {fname} in {_format_elapsed(elapsed)}")
        fname += ".singlessol"
        path = os.path.join("solutions", fname)
        write_file(path, solution, seed, f"Solved in {_format_elapsed(elapsed)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hitori SMT solver and checker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser("solve", help="Solve puzzle(s) using the SMT solver")
    group_solve = solve_parser.add_mutually_exclusive_group(required=True)
    group_solve.add_argument("-f", "--file", type=str, help="Path to a puzzle file")
    group_solve.add_argument("-d", "--folder", type=str, help="Path to folder containing puzzle files")
    solve_parser.set_defaults(func=_solve_command)

    check_parser = subparsers.add_parser("check", help="Check solution(s) for correctness")
    group_check = check_parser.add_mutually_exclusive_group(required=True)
    group_check.add_argument("-f", "--file", type=str, help="Path to a solution file")
    group_check.add_argument("-d", "--folder", type=str, help="Path to folder containing solution files")
    check_parser.set_defaults(func=_check_command)

    args = parser.parse_args()
    args.func(args)