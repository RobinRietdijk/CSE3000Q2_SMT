
import math
import numpy as np
from collections import Counter
from file_utils import read_puzzle
from scipy.stats import mannwhitneyu, false_discovery_control, spearmanr

def _flatten_results(results: list) -> list:
    """ Flatten the results from multiple runs

    Args:
        results (list): Results from the experiments

    Returns:
        list: A flattened list of results
    """
    by_puzzle = {}

    for r in results:
        key = (r["solver"], r["size"], r["puzzle"])
        if key not in by_puzzle:
            by_puzzle[key] = {
                "solver": r["solver"],
                "size": r["size"],
                "path": r["path"],
                "puzzle": r["puzzle"],
                "puzzle_statistics": r["puzzle_statistics"],
                "statistics": {
                    "runtime": [],
                    "decisions": [],
                    "conflicts": [],
                    "propagations": []
                }
            }
        by_puzzle[key]["statistics"]["runtime"].append(r["statistics"]["runtime"])
        by_puzzle[key]["statistics"]["decisions"].append(r["statistics"]["decisions"])
        by_puzzle[key]["statistics"]["conflicts"].append(r["statistics"]["conflicts"])
        by_puzzle[key]["statistics"]["propagations"].append(r["statistics"]["propagations"])

    flattened = []
    for r in by_puzzle.values():
        statistics = r["statistics"]
        median = {k: float(np.median(v)) if len(v) else 0.0 for k, v in statistics.items()}
        r["statistics"] = median
        r["runs"] = len(statistics["runtime"])
        flattened.append(r)

    return flattened

def _build_groups(results: list, runtime_outliers: list, effort_outliers: list) -> tuple:
    """ Build groups of puzzles based on the outlier sets

    Args:
        results (list): Results from the experiments
        runtime_outliers (list): Outliers gathered from the runtime filtering method
        effort_outliers (list): Outliers gathered from the effort filtering method

    Returns:
        tuple: 4 sets based on the outliers from each method
    """
    runtime_puzzles = {r["puzzle"] for r in runtime_outliers}
    effort_puzzles = {r["puzzle"] for r in effort_outliers}

    runtime_only = []
    effort_only = []
    neither = []
    both = []

    for r in results:
        id = r["puzzle"]
        in_runtime = id in runtime_puzzles
        in_effort = id in effort_puzzles

        if in_runtime and in_effort:
            both.append(r)
        elif in_runtime:
            runtime_only.append(r)
        elif in_effort:
            effort_only.append(r)
        else:
            neither.append(r)
        
    return runtime_only, effort_only, neither, both

def _group_by_size(flattened_results: list) -> dict:
    """ Group the results by puzzle size

    Args:
        flattened_results (list): flattened list of results from the experiments

    Returns:
        dict: results grouped by puzzle size
    """
    groups = {}
    for r in flattened_results:
        key = r["size"]
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
    return groups

def _iqr_whiskers(x: list, k: float = 1.5) -> tuple:
    """ Calculate the IQR whiskers of a list

    Args:
        x (list): List of which to calculate the whiskers are for
        k (float, optional): Scalar for the whiskers. Defaults to 1.5.

    Returns:
        tuple: bottom and upper whiskers of the list
    """
    q1 = np.percentile(x, 25)
    q3 = np.percentile(x, 75)
    iqr = q3-q1
    return q1-k*iqr, q3+k*iqr

def _effort_score(r: dict, weights: dict) -> float:
    """ Calculates an effort based score for the results

    Args:
        r (dict): Results from the experiments
        weights (dict): Dict of weights for the effort statistics

    Returns:
        float: Effort score which is a weighted sum of statistics
    """
    return (
        weights["decisions"]*math.log1p(r["statistics"]["decisions"])+
        weights["conflicts"]*math.log1p(r["statistics"]["conflicts"])+
        weights["propagations"]*math.log1p(r["statistics"]["propagations"])
    )

def _find_effort_outliers(results: list, weights: dict, k: float) -> list:
    """ Finds the outliers using the effort based method

    Args:
        results (list): Results from the experiments
        weights (dict): Weights to be used for the effort score
        k (float): Scalar to be used for the IQR whiskers

    Returns:
        list: List of outliers in this set of results based on effort score
    """
    scores = [(r, _effort_score(r, weights)) for r in results]
    values = [s for _, s in scores]

    if len(values) < 8:
        return []

    _, upper = _iqr_whiskers(values, k)
    return [r for r, s in scores if s > upper]

def _find_runtime_outliers(results: list, k: float) -> list:
    """ Finds the outliers using the runtime based method

    Args:
        results (list): Results from the experiments
        k (float): Scalar to be used for the IQR whiskers

    Returns:
        list: List of outliers in this set of results based on runtime score
    """
    values = [math.log1p(r["statistics"]["runtime"]) for r in results]

    if len(values) < 8:
        return []

    _, upper = _iqr_whiskers(values, k)
    return [r for r in results if math.log1p(r["statistics"]["runtime"]) > upper]

def _find_pairs_and_triplets(puzzle: list, n: int) -> tuple[int, int]:
    """ Find the number of pairs and triplets in a puzzle

    Args:
        puzzle (list): Puzzle grid
        n (int): Size of the puzzle

    Returns:
        tuple[int, int]: Tuple containing the number of pairs and triplets
    """
    pairs = 0
    triplets = 0
    for i in range(n):
        j = 0
        while j < n-1:
            if puzzle[i][j] == puzzle[i][j+1]:
                if j < n-2 and puzzle[i][j] == puzzle[i][j+2]:
                    triplets += 1
                    j += 3
                else:
                    pairs += 1
                    j += 2
            else:
                j += 1
        j = 0
        while j < n-1:
            if puzzle[j][i] == puzzle[j+1][i]:
                if j < n-2 and puzzle[j][i] == puzzle[j+2][i]:
                    triplets += 1
                    j += 3
                else:
                    pairs += 1
                    j += 2
            else:
                j += 1
    return pairs, triplets

def _find_isolated(puzzle: list, n: int) -> int:
    """ Finds the number of isolated duplicates in a puzzle

    Args:
        puzzle (list): Puzzle grid
        n (int): Size of the puzzle

    Returns:
        int: The number of isolated duplicates
    """
    isolated = 0
    for i in range(n):
        row_map = {}
        col_map = {}
        k = 0
        while k < n:
            nk = k
            if k < n-1 and puzzle[i][k] == puzzle[i][k+1]:
                if k < n-2 and puzzle[i][k] == puzzle[i][k+2]:
                    nk += 3
                else:
                    nk += 2
            else:
                nk += 1

            v = puzzle[i][k]
            row_map[v] = row_map.get(v, 0)+1
            k = nk
        
        k = 0
        while k < n:
            nk = k
            if k < n-1 and puzzle[k][i] == puzzle[k+1][i]:
                if k < n-2 and puzzle[k][i] == puzzle[k+2][i]:
                    nk += 3
                else:
                    nk += 2
            else:
                nk += 1

            v = puzzle[k][i]
            col_map[v] = col_map.get(v, 0)+1
            k = nk
        
        for _, val in row_map.items():
            if val > 1:
                isolated += 1
        for _, val in col_map.items():
            if val > 1:
                isolated += 1
    return isolated

def _cross_duplicates(puzzle: list, n: int) -> int:
    """ Number of entangled duplicates in the puzzle

    Args:
        puzzle (list): Puzzle grid
        n (int): Size of the puzzle

    Returns:
        int: Number of entangled duplicates
    """
    rows = [[False]*n for _ in range(n)]
    cols = [[False]*n for _ in range(n)]

    for i in range(n):
        count = Counter(puzzle[i])
        for j in range(n):
            if count[puzzle[i][j]] > 1:
                rows[i][j] = True

    for i in range(n):
        col = [puzzle[j][i] for j in range(n)]
        count = Counter(col)
        for j in range(n):
            if count[puzzle[j][i]] > 1:
                cols[j][i] = True
    
    return sum(1 for i in range(n) for j in range(n) if rows[i][j] and cols[i][j])        

def analyze_puzzle_statistics(results: list) -> dict:
    """ Analyses a puzzle for certain patterns and statistics

    Args:
        results (list): Results from the experiments

    Returns:
        dict: A dict containing the statistics per puzzle per size
    """
    puzzle_dict = {}
    for r in results:
        path = r["path"]
        (_, puzzle, _) = read_puzzle(path, False)
        fname = r["puzzle"]
        n = r["size"]
        if n not in puzzle_dict:
            puzzle_dict[n] = {}
        
        stats = {}
        stats["path"] = path

        pairs, triplets = _find_pairs_and_triplets(puzzle, n)
        isolated = _find_isolated(puzzle, n)
        cross_duplicates = _cross_duplicates(puzzle, n)

        stats["pair_duplicates"] = pairs
        stats["triple_duplicates"] = triplets
        stats["isolated_duplicates"] = isolated
        stats["cross_duplicates"] = cross_duplicates
        stats["black_cells"] = r["puzzle_statistics"]["black_cells"]
        puzzle_dict[n][fname] = stats
    return puzzle_dict

def _extract_features(puzzle_stats: dict, size: int, group: list, feature: str) -> list:
    """ Extract a certain puzzle feature from a puzzle group

    Args:
        puzzle_stats (dict): Statistics of the puzzles
        size (int): Size of the puzzle
        group (list): Group of which to extract stats from
        feature (str): Feature to extract from group

    Returns:
        list: List of values for the feature in the group specified
    """
    group_puzzle_names = [g["puzzle"] for g in group]
    return [puzzle_stats[size][puzzle][feature] for puzzle in group_puzzle_names]

def run_all(results: list, solver: str = "qf_ia", k_out: float = 1.5, k_fout: float = 3.0) -> None:
    """ Run all analysis

    Args:
        results (list): Results from the experiments
        solver (str, optional): Solver that was used for evaluation. Defaults to "qf_ia".
        k_out (float, optional): Scalar that is used for the IQR whiskers. Defaults to 1.5.
        k_fout (float, optional): Scalar that is used for the far-out IQR whiskers. Defaults to 3.0.
    """
    results = [r for r in results if r["solver"] == solver]
    results = _flatten_results(results)
    puzzle_statistics_by_size = analyze_puzzle_statistics(results)
    grouped = _group_by_size(results)
    weights = {
        "decisions": 1.0,
        "conflicts": 0.7,
        "propagations": 0.5,
    }

    # Gather outliers
    all_outliers_runtime = {}
    all_outliers_effort = {}
    for size, r in sorted(grouped.items()):
        far_out_runtime = _find_runtime_outliers(r, k_fout)
        outliers_runtime = _find_runtime_outliers(r, k_out)
        all_outliers_runtime[size] = {"outliers": outliers_runtime, "far_out": far_out_runtime}

        far_out_effort = _find_effort_outliers(r, weights, k_fout)
        outliers_effort = _find_effort_outliers(r, weights, k_out)
        all_outliers_effort[size] = {"outliers": outliers_effort, "far_out": far_out_effort}
    
    features = ["pair_duplicates", "triple_duplicates", "isolated_duplicates", "cross_duplicates", "black_cells"]
    for size, rs in sorted(grouped.items()):
        runtime_only, effort_only, neither, both = _build_groups(rs, all_outliers_runtime[size]["outliers"], all_outliers_effort[size]["outliers"])
        print(f"Filtered groups ({size}x{size}) | runtime_only={len(runtime_only)} | effort_only={len(effort_only)} | both={len(both)} | neither={len(neither)}")

        if len(neither) < 5:
            continue

        if len(runtime_only) >= 5:
            runtime_tests = []
            # Extract a feature from the base and runtime set and use the MannWhitneyU test to check significance
            for feature in features:
                base = _extract_features(puzzle_statistics_by_size, size, neither, feature)
                a = _extract_features(puzzle_statistics_by_size, size, runtime_only, feature)
                
                if len(base) < 5 or len(a) < 5:
                    continue

                U, p = mannwhitneyu(a, base, alternative="two-sided")
                runtime_tests.append((feature, float(p), float(np.median(a)), float(np.median(base)), float(np.mean(a)), float(np.mean(base))))
            
            if runtime_tests:
                p_values = [test[1] for test in runtime_tests]
                adjusted_p = false_discovery_control(p_values, method="bh")
                
                print("runtime_only vs neither:")
                for (feature, p, med_a, med_b, avg_a, avg_b), q in zip(runtime_tests, adjusted_p):
                    star = " *" if q < 0.05 else ""
                    print(f"{feature:20s} med={med_a:.2f}, avg={avg_a:.2f} vs {med_b:.2f}, avg={avg_b:.2f} | p={p:.3g} | q={q:.3g}{star}")

        if len(effort_only) >= 5:
            effort_tests = []
            # Extract a feature from the base and effort set and use the MannWhitneyU test to check significance
            for feature in features:
                base = _extract_features(puzzle_statistics_by_size, size, neither, feature)
                a = _extract_features(puzzle_statistics_by_size, size, effort_only, feature)

                if len(base) < 5 or len(a) < 5:
                    continue

                U, p = mannwhitneyu(a, base, alternative="two-sided")
                effort_tests.append((feature, float(p), float(np.median(a)), float(np.median(base)), float(np.mean(a)), float(np.mean(base))))

            if effort_tests:
                p_values = [test[1] for test in effort_tests]
                adjusted_p = false_discovery_control(p_values, method="bh")

                print("effort_only vs neither:")
                for (feature, p, med_b, med_base, avg_a, avg_b), q in zip(effort_tests, adjusted_p):
                    star = " *" if q < 0.05 else ""
                    print(f"{feature:20s} med={med_a:.2f}, avg={avg_a:.2f} vs {med_b:.2f}, avg={avg_b:.2f} | p={p:.3g} | q={q:.3g}{star}")

    print("Spearman rank correlations:")
    for size, result in sorted(grouped.items()):
        print(f"Size {size}x{size}")

        effort_values = [_effort_score(r, weights) for r in result]
        runtime_values = [r["statistics"]["runtime"] for r in result]

        for feature in features:
            feat_vals = [puzzle_statistics_by_size[size][r["puzzle"]][feature] for r in result]

            rho_effort, p_effort = spearmanr(feat_vals, effort_values)
            rho_runtime, p_runtime = spearmanr(feat_vals, runtime_values)
            print(f"{feature:20s} rho_eff={rho_effort: .3f} (p={p_effort:.3g}) | rho_run={rho_runtime: .3f} (p={p_runtime:.3g})")


    