import numpy as np
import scipy.stats
import matplotlib.pyplot as plt
from copy import deepcopy
import os
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as patches

def _flatten_results(results: list) -> list:
    grouped = {}
    for r in results:
        key = (r["solver"], r["size"], r["puzzle"])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(r)
    
    flattened = []
    for (solver, size, puzzle), rs in grouped.items():
        base = deepcopy(rs[0])
        runtimes = [float(r["statistics"]["runtime"]) for r in rs]
        base["statistics"]["runtime"] = float(np.median(runtimes))

        encoding_keys = rs[0]["statistics"]["encoding_size"]
        encoding_sizes = {}
        for key in encoding_keys.keys():
            values = [float(r["statistics"]["encoding_size"][key]) for r in rs]
            if values:
                base["statistics"]["encoding_size"][key] = float(np.median(values))
        flattened.append(base)
    return flattened

def _encoding_total(r: dict) -> int:
    enc = r["statistics"]["encoding_size"]
    vars = sum(enc[k] for k in enc.keys() if k != "assertions")
    return int(vars+enc["assertions"])

def _short_label(name: str, baseline: str) -> str:
    prefix = baseline+"+"
    return name[len(prefix):] if name.startswith(prefix) else name

def _order_constraints(matrix: dict, relevance: dict, baseline: str) -> list:
    def stats(c: str):
        significant_sizes = relevance[c]["sizes"]
        dirs = [matrix[c][n][1] for n in significant_sizes]
        faster = sum(1 for d in dirs if d==1)
        slower = sum(1 for d in dirs if d==-1)
        mixed = (faster > 0 and slower > 0)
        relevant = relevance[c]["relevant"]

        return relevant, faster, slower, mixed, len(significant_sizes)
    def key(c: str):
        relevant, faster, slower, mixed, k = stats(c)
        if faster > 0:
            group = 0
        elif mixed:
            group = 1
        elif relevant:
            group = 2
        else:
            group = 3
        
        return (group, -k, -faster, -slower, _short_label(c, baseline))
    
    return sorted(matrix.keys(), key=key)

def _pair_by_size(results: list, size: int, this_name: str, that_name: str) -> tuple:
    this = {}
    that = {}

    for r in results:
        if r["size"] != size:
            continue
        puzzle = r["puzzle"]
        solver = r["solver"]
        if solver == this_name:
            this[puzzle] = r["statistics"]["runtime"]
        elif solver == that_name:
            that[puzzle] = r["statistics"]["runtime"]
    common = sorted(set(this.keys()) & set(that.keys()))
    if not common:
        return np.array([], dtype=float), np.array([], dtype=float)
    
    this_common = np.array([this[p] for p in common], dtype=float)
    that_common = np.array([that[p] for p in common], dtype=float)
    return this_common, that_common

def _pair_median_runtime_by_size(results: list, size: int, baseline: str, solver: str) -> tuple[float, float, int]:
    s_base, s_var = _pair_by_size(results, size, baseline, solver)
    if len(s_base) == 0:
        return (float("nan"), float("nan"), 0)
    return (float(np.median(s_base)), float(np.median(s_var)), int(len(s_base)))

def _holm_correction(p_values: dict, alpha: float) -> dict:
    keys = list(p_values.keys())
    ps = np.array([p_values[k] for k in keys], dtype=float)

    ps[np.isnan(ps)] = 1.0
    order = np.argsort(ps)
    m = len(ps)

    rejected = {k: False for k in keys}
    for i, index in enumerate(order):
        if ps[index] <= alpha/(m-i):
            rejected[keys[index]] = True
        else:
            break
    
    return rejected

def _classify_constraints(matrix: dict, alpha: float):
    relevance = {}

    for c, sizes in matrix.items():
        p_values = {n: sizes[n][0] for n in sizes}
        rejected = _holm_correction(p_values, alpha)
        significant_sizes = [k for k, v in rejected.items() if v]

        relevance[c] = {
            "relevant": len(significant_sizes) > 0,
            "sizes": significant_sizes,
            "directions": {n: sizes[n][1] for n in significant_sizes}
        }
    
    return relevance

def _significance_grid(matrix: dict, relevance: dict, baseline: str) -> tuple:
    constraint_order = _order_constraints(matrix, relevance, baseline) 
    size_order = sorted({n for c in matrix for n in matrix[c].keys()})
    grid = np.zeros((len(constraint_order), len(size_order)), dtype=int)

    for i, c in enumerate(constraint_order):
        significant = set(relevance[c]["sizes"])
        for j, n in enumerate(size_order):
            if n in significant:
                grid[i, j] = int(matrix[c][n][1])

    constraint_labels = [_short_label(c, baseline) for c in constraint_order]
    return constraint_order, constraint_labels, size_order, grid

def _wilcoxon_by_constraint(results: list, baseline: str, constraints: list|None, sizes: list|None) -> dict:
    if constraints is None:
        constraints = sorted({r["solver"] for r in results if r["solver"] != baseline})
    if sizes is None:
        sizes = sorted({r["size"] for r in results})
    
    # Created a matrix for wicoxon signed-rank tests by constraints by sizes
    matrix = {c: {} for c in constraints}

    for c in constraints:
        for n in sizes:
            s1, s2 = _pair_by_size(results, n, baseline, c)
            if len(s1) == 0 or len(s2) == 0:
                matrix[c][n] = (np.nan, 0)
                continue

            difference  = s2 - s1
            median_difference = float(np.median(difference))
            direction = 0
            if median_difference < 0:
                direction = 1
            elif median_difference > 0:
                direction = -1
            
            try:
                stat = scipy.stats.wilcoxon(s1, s2)
                p = float(stat.pvalue)
            except ValueError:
                p = 1.0
                direction = 0
            
            matrix[c][n] = (p, direction)
    return matrix

def _print_wolcoxon(relevance: dict) -> None:
    relevant = [(c, r) for c, r in relevance.items() if r["relevant"]]
    not_relevant = [(c, r) for c, r in relevance.items() if not r["relevant"]]

    relevant.sort(key=lambda x: (-len(x[1]["sizes"]), x[0]))
    not_relevant.sort(key=lambda x: x[0])

    print("\n=== RQ2 Wilcoxon screening (Holm-corrected across sizes) ===")
    print(f"Relevant constraints: {len(relevant)} / {len(relevance)}")
    print(f"Irrelevant constraints: {len(not_relevant)} / {len(relevance)}")

    max_list = 10**9

    if not_relevant:
        print("\n-- Irrelevant (no significant size) --")
        for c, _ in not_relevant[:max_list]:
            print(f"  {c}")
        if len(not_relevant) > max_list:
            print(f"  ... ({len(not_relevant) - max_list} more)")

    if relevant:
        print("\n-- Relevant (significant at ≥1 size) --")
        for c, r in relevant[:max_list]:
            parts = []
            for n in r["sizes"]:
                d = r["directions"].get(n, 0)
                parts.append(f"{n}:{'faster' if d == 1 else 'slower' if d == -1 else 'n/a'}")
            print(f"  {c}: {', '.join(parts)}")
        if len(relevant) > max_list:
            print(f"  ... ({len(relevant) - max_list} more)")

def _plot_significance_heatmap(constraint_labels: list, size_order: list, significance_grid: np.ndarray) -> None:
    n_rows, n_cols = significance_grid.shape
    fig_h = max(2.6, 0.32*n_rows+1.2)
    fig_w = max(6.0, 0.38*n_cols+2.2)
    cmap = ListedColormap(["#2B59C3", "#FFFFFF", "#D1495B"]) 
    norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap.N)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.grid(False)
    ax.minorticks_off()
    x = np.arange(n_cols+1)
    y = np.arange(n_rows+1)
    m = ax.pcolormesh(x, y, significance_grid, cmap=cmap, norm=norm, shading="flat", edgecolors="0.85", linewidth=0.6)

    ax.invert_yaxis()
    ax.set_yticks(np.arange(n_rows)+0.5)
    ax.set_xticks(np.arange(n_cols)+0.5)
    ax.set_xticklabels([str(n) for n in size_order], fontsize=7)
    ax.set_yticklabels(constraint_labels, fontsize=7)
    ax.tick_params(axis="x", bottom=True, labelbottom=True, length=2.5, width=0.6)
    ax.tick_params(axis="y", left=True, labelleft=True)

    ax.set_xlabel("Puzzle size (n)")
    ax.set_ylabel("Redundant constraint")
    ax.set_title("Wilcoxon vs baseline: significant slower / n.s. / faster", fontsize=8)

    full_slower_rows = [i for i in range(n_rows) if np.all(significance_grid[i, :] == -1)]
    for i in full_slower_rows:
        # row i spans y in [i, i+1], and x in [0, n_cols]
        rect = patches.Rectangle(
            (0, i), n_cols, 1,
            facecolor="white",
            alpha=0.55,      # how much to fade
            edgecolor="none",
            zorder=3         # above cells, below edges/ticks (ticks are zorder higher anyway)
        )
        ax.add_patch(rect)

    cbar = fig.colorbar(m, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_ticks([-1, 0, 1])
    cbar.set_ticklabels(["slower", "n.s.", "faster"])
    cbar.ax.tick_params(labelsize=6)

    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.14, top=0.92)
    out_path = os.path.join(os.path.abspath("plots"), f"heatmap.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")

def summarize_speedup_by_constraint(results: list, baseline: str, constraints: list | None = None, sizes: list | None = None) -> dict:
    if constraints is None:
        constraints = sorted({r["solver"] for r in results if r["solver"] != baseline})
    if sizes is None:
        sizes = sorted({r["size"] for r in results})

    out = {c: {} for c in constraints}

    for c in constraints:
        for n in sizes:
            base_med, var_med, pairs = _pair_median_runtime_by_size(results, n, baseline, c)
            if pairs == 0 or not np.isfinite(base_med) or not np.isfinite(var_med) or var_med <= 0:
                out[c][n] = {
                    "pairs": pairs,
                    "baseline_median": base_med,
                    "solver_median": var_med,
                    "speedup": float("nan"),
                    "delta": float("nan"),
                }
                continue

            out[c][n] = {
                "pairs": pairs,
                "baseline_median": base_med,
                "solver_median": var_med,
                "speedup": float(base_med / var_med),
                "delta": float(var_med - base_med),
            }

    return out

def summarize_encoding_ratio_by_constraint(results: list, baseline: str, constraints: list | None = None, sizes: list | None = None) -> dict:
    if constraints is None:
        constraints = sorted({r["solver"] for r in results if r["solver"] != baseline})
    if sizes is None:
        sizes = sorted({r["size"] for r in results})

    # collect totals
    totals = {}  # totals[solver][size] = [total,...]
    for r in results:
        s = r["solver"]
        n = r["size"]
        if s != baseline and s not in constraints:
            continue
        if n not in sizes:
            continue
        totals.setdefault(s, {}).setdefault(n, []).append(_encoding_total(r))

    out = {c: {} for c in constraints}

    for c in constraints:
        for n in sizes:
            base_list = totals.get(baseline, {}).get(n, [])
            var_list = totals.get(c, {}).get(n, [])
            if not base_list or not var_list:
                out[c][n] = {"baseline_total": None, "solver_total": None, "ratio": float("nan")}
                continue

            base_med = int(np.median(np.array(base_list, dtype=float)))
            var_med = int(np.median(np.array(var_list, dtype=float)))
            ratio = float(var_med / base_med) if base_med > 0 else float("nan")

            out[c][n] = {"baseline_total": base_med, "solver_total": var_med, "ratio": ratio}

    return out

def print_constraint_summary(speedup: dict, enc: dict, *, sizes: list[int] | None = None, baseline: str = "qf_ia") -> None:
    # infer sizes
    if sizes is None:
        sizes = sorted({n for c in speedup for n in speedup[c].keys()})

    if not sizes:
        print("No sizes found.")
        return

    n_max = max(sizes)

    print("\n=== RQ2 constraint summary (speedup + encoding ratio) ===")
    print(f"Baseline: {baseline}")
    print(f"Sizes: {sizes} (max n={n_max})")

    for c in sorted(speedup.keys()):
        vals = []
        for n in sizes:
            v = speedup[c].get(n, {}).get("speedup", float("nan"))
            if np.isfinite(v):
                vals.append((n, v))

        best = max(vals, key=lambda t: t[1]) if vals else (None, float("nan"))
        worst = min(vals, key=lambda t: t[1]) if vals else (None, float("nan"))

        s_at_max = speedup[c].get(n_max, {}).get("speedup", float("nan"))
        e_at_max = enc.get(c, {}).get(n_max, {}).get("ratio", float("nan"))

        print(f"\n{c}:")
        print(f"  best speedup:  n={best[0]}  {best[1]:.3g}x")
        print(f"  worst speedup: n={worst[0]}  {worst[1]:.3g}x")
        print(f"  speedup@{n_max}: {s_at_max:.3g}x")
        print(f"  enc_ratio@{n_max}: {e_at_max:.3g}x")

def run_wilcoxon(results: list, baseline: str, constraints: list|None = None, sizes: list|None = None, alpha: float = 0.05, print_results: bool = True) -> None:
    flattened_results = _flatten_results(results)
    matrix = _wilcoxon_by_constraint(flattened_results, baseline, constraints, sizes)
    relevance = _classify_constraints(matrix, alpha)

    constraint_order, constraint_labels, size_order, significance_grid = _significance_grid(matrix, relevance, baseline)
    if print_results:
        _print_wolcoxon(relevance)
    _plot_significance_heatmap(constraint_labels, size_order, significance_grid)
    speedup = summarize_speedup_by_constraint(flattened_results, baseline, constraints, sizes)
    enc = summarize_encoding_ratio_by_constraint(flattened_results, baseline, constraints, sizes)

    print_constraint_summary(speedup, enc, sizes=size_order, baseline=baseline)
