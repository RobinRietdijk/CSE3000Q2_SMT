from collections import deque
from file_utils import read_solution_dir, read_solution

def check_puzzle(puzzle: list) -> bool:
    n = len(puzzle)
    rows = [set() for _ in range(n)]
    cols = [set() for _ in range(n)]
    num_white = 0
    start = None

    for i in range(n):
        for j in range(n):
            val = puzzle[i][j]
            if val.endswith("B"):
                if i+1 < n:
                    if puzzle[i+1][j].endswith("B"):
                        return False
                if j+1 < n:
                    if puzzle[i][j+1].endswith("B"):
                        return False
                continue
            if start is None:
                start = (i, j)

            if val in rows[i] or val in cols[j]:
                return False
            rows[i].add(val)
            cols[j].add(val)
            num_white += 1

    if num_white == 0 or start is None:
        return False

    visited = set([start])
    queue = deque([start])

    while queue:
        i, j = queue.popleft()
        for di, dj in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            ni, nj = i+di, j+dj
            if 0 <= ni < n and 0 <= nj < n:
                if puzzle[ni][nj].endswith("B"):
                    continue
                if (ni, nj) not in visited:
                    visited.add((ni, nj))
                    queue.append((ni, nj))

    return len(visited) == num_white


def check_file(path: str) -> tuple[str, bool]:
    fname, grid, _ = read_solution(path)
    result = check_puzzle(grid)
    if result:
        print(f"{fname}: Correct solution")
    else:
        print(f"{fname}: Incorrect solution")
    return fname, result

def check_folder(path: str) -> list[tuple[str, bool]]:
    solutions = read_solution_dir(path)
    all_results = []
    for fname, grid, _ in solutions:
        result = check_puzzle(grid)
        if result:
            print(f"{fname}: Correct solution")
        else:
            print(f"{fname}: Incorrect solution")
        all_results.append((fname, result))
    return all_results

if __name__ == "__main__":
    print(check_folder("solutions"))