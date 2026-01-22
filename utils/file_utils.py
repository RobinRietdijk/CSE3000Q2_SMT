import os
import sys
import csv

PUZZLE_EXTENSIONS = [".singles"]
SOLUTION_EXTENSIONS = [".singlessol"]

def _is_puzzle(path: str) -> bool:
    """ Finds out if the path is to a puzzle file by checking the extension

    Args:
        path (str): Path to the file

    Returns:
        bool: True if the path is a puzzle file
    """
    _, ext = os.path.splitext(path)
    return ext.lower() in PUZZLE_EXTENSIONS

def _is_solution(path: str) -> bool:
    """ Finds out if the path is to a solution file by checking the extension

    Args:
        path (str): Path to the file

    Returns:
        bool: True if the path is a solution file
    """
    _, ext = os.path.splitext(path)
    return ext.lower() in SOLUTION_EXTENSIONS

def _parse_file(path: str) -> tuple[list, str|None]:
    """ Extracts the grid and seed from a file.

    Args:
        path (str): Path to the file

    Returns:
        tuple[list, str|None]: _description_
    """
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

def _read_file(path: str, puzzles: bool, strict: bool) -> list:
    """ Reads a file

    Args:
        path (str): Path to the file
        puzzles (bool): Flag to indicate whether we want to read a puzzle or solution file
        strict (bool): Flag to indicate if we want to exit with an error when the file is not correct

    Returns:
        list: List containing a single tuple of the file that was read
    """
    if not os.path.exists(path):
        sys.exit(f"Error: File does not exist at {path}")
    if (puzzles and not _is_puzzle(path)) or (not puzzles and not _is_solution(path)):
        if strict:
            sys.exit(f"Error: Not a {'puzzle' if puzzles else 'solution'} file at {path}")
        else:
            print(f"Warning: Not a {'puzzle' if puzzles else 'solution'} file at {path}")
            return []

    grid, seed = _parse_file(path)
    return [(path, grid, seed)]

def _read_dir(path: str, puzzles: bool, strict: bool, recursive: bool) -> list:
    """ Reads a directory

    Args:
        path (str): Path to the directory
        puzzles (bool): Flag to indicate whether we want to read puzzle or solution file
        strict (bool): Flag to indicate if we want to exit with an error when the file is not correct
        recursive (bool): Flag to indicate whether we want to look recursively within folders

    Returns:
        list: List of tuples containing puzzle or solution file data
    """
    if not os.path.isdir(path):
        sys.exit(f"Error: Not a directory at {path}")

    grids = []
    for filename in os.listdir(path):
        file = os.path.join(path, filename)

        if not os.path.isfile(file):
            if recursive:
                grids.extend(_read_dir(file, puzzles, strict, recursive))
            continue

        grids.extend(_read_file(file, puzzles, strict))
    return grids

def _flatten_dict(dictionary: dict, parent_key: str = "", seperator: str = ".") -> dict:
    """ Flatten a dictionary into a single layer instead from nested dictionaries

    Args:
        dictionary (dict): Dictionary to flatten
        parent_key (str, optional): Parent key of the nested dictionary. Defaults to "".
        seperator (str, optional): seperator used in the new keys. Defaults to ".".

    Returns:
        dict: Flattened 1-dimensional dictionary
    """
    items = {}
    for key, value in dictionary.items():
        new_key = f"{parent_key}{seperator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(_flatten_dict(value, new_key, seperator))
        else:
            items[new_key] = value
    return items

def _unflatten_dict(dictionary: dict, seperator: str = ".") -> dict:
    """ Unflattens a dictionary back to its original form

    Args:
        dictionary (dict): Dictionary to unflatten
        seperator (str, optional): Seperator that was used when flattening previous dictionary. Defaults to ".".

    Returns:
        dict: Unflattend dictionary
    """
    result = {}
    for key, value in dictionary.items():
        if value in ("", None):
            continue

        parts = key.split(seperator)
        current = result
        for p in parts[:-1]:
            current = current.setdefault(p, {})
        current[parts[-1]] = value
    return result

def _cast(value: str) -> str|int|float|None:
    """ Cast a string to either an Integer or Float value

    Args:
        value (str): Value to be cast

    Returns:
        str|int|float|None: Casted value
    """
    if value is None or value == "":
        return None
    try:
        i = int(value)
        if str(i) == value:
            return i
    except:
        pass
    try:
        return float(value)
    except:
        return value

def read_puzzle(path: str, strict: bool) -> tuple[str, list, str]:
    """ Read a puzzle file

    Args:
        path (str): Path to puzzle file
        strict (bool): Flag to indicate if we want to exit with an error when the file is not correct

    Returns:
        tuple[str, list, str]: Tuple containing the contents of the puzzle file
    """
    result = _read_file(path, True, strict)
    if not result:
        sys.exit(f"Error: No puzzle file found at {path}")
    return result[0]

def read_solution(path: str, strict: bool) -> tuple[str, list, str]:
    """ Read a solution file

    Args:
        path (str): Path to the solution file
        strict (bool): Flag to indicate if we want to exit with an error when the file is not correct

    Returns:
        tuple[str, list, str]: Tuple containing the contents of the solution file
    """
    result = _read_file(path, False, strict)
    if not result:
        sys.exit(f"Error: No solution file found at {path}")
    return result[0]

def read_puzzle_dir(path: str, recursive: bool, strict: bool) -> list:
    """ Read a puzzle directory

    Args:
        path (str): Path to the puzzle directory
        recursive (bool): Flag to indicate whether we want to look recursively within folders
        strict (bool): Flag to indicate if we want to exit with an error when the file is not correct

    Returns:
        list: List of tuples containing puzzle information
    """
    puzzles = _read_dir(path, True, strict, recursive)
    if not puzzles:
        sys.exit(f"Error: No puzzle files found in {path}")
    return puzzles

def read_solution_dir(path: str, recursive: bool, strict: bool) -> list:
    """ Read a solution directory

    Args:
        path (str): Path to the puzzle directory
        recursive (bool): Flag to indicate whether we want to look recursively within folders
        strict (bool): Flag to indicate if we want to exit with an error when the file is not correct

    Returns:
        list: List of tuples containing solution information
    """
    solutions = _read_dir(path, False, strict, recursive)
    if not solutions:
        sys.exit(f"Error: No solution files found in {path}")
    return solutions

def write_file(path: str, puzzle: list, seed: str|None, extra: str|None) -> None:
    """ Writes a solution to a file

    Args:
        path (str): Path of the solution file
        puzzle (list): Puzzle solution to be written to the file
        seed (str | None): Seed to be written to the file
        extra (str | None): Additional comments to be written to the file
    """
    with open(path, "w") as file:
        file.write(f"{len(puzzle)}\n\n")
        for row in puzzle:
            file.write(" ".join(map(str, row)) + "\n")
        if seed is not None:
            file.write(f"\n@{seed}")
        if extra is not None:
            for line in extra.splitlines():
                file.write(f"\n#{line}")

def append_comment(path: str, comment: str) -> None:
    """ Append a comment to a file

    Args:
        path (str): Path to the file to be edited
        comment (str): Comment to be added to the file
    """
    with open(path, "a") as file:
        for line in comment.splitlines():
            file.write(f"\n#{line}")

def write_csv(results: dict, out_dir: str) -> None:
    """ Write results to a csv directory

    Args:
        results (dict): Results from an experiment
        out_dir (str): Directory to write to
    """
    os.makedirs(out_dir, exist_ok=True)
    by_solver = {}
    for r in results:
        by_solver.setdefault(r["solver"], []).append(r)

    for solver, solver_results in by_solver.items():
        out_path = os.path.join(out_dir, f"{solver}.csv")

        flat_rows = []
        fieldnames = set()

        for r in solver_results:
            flat = _flatten_dict(r)
            flat_rows.append(flat)
            fieldnames.update(flat.keys())

        fieldnames = sorted(fieldnames)

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for flat in flat_rows:
                writer.writerow(flat)

def read_csv(path: str) -> dict:
    """ Read a csv file

    Args:
        path (str): Csv file to be read

    Returns:
        dict: Results read from a csv file
    """
    if not os.path.exists(path):
        sys.exit(f"Error: File does not exist at {path}")

    results = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            casted = {key: _cast(value) for key, value in row.items()}
            results.append(_unflatten_dict(casted))

    return results

def read_csv_folder(path: str, strict: bool, recursive: bool) -> list:
    """ Read an entire folder of csv files

    Args:
        path (str): Csv folder to be read
        strict (bool): Flag to indicate if we want to exit with an error when the file is not correct
        recursive (bool): Flag to indicate whether we want to look recursively within folders

    Returns:
        list: List of results read from the csv folder
    """
    if not os.path.isdir(path):
        sys.exit(f"Error: Not a directory at {path}")

    csvs = []
    for filename in os.listdir(path):
        file = os.path.join(path, filename)

        if not os.path.isfile(file):
            if recursive:
                csvs.extend(read_csv_folder(file, strict, recursive))
            continue

        csvs.extend(read_csv(file))
    return csvs