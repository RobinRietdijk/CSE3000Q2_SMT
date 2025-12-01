import os
import matplotlib.pyplot as plt

def _plot_puzzleruntime(results):
    by_size = {}
    for r in results:
        size = r["size"]
        if size not in by_size:
            by_size[size] = []
        by_size[r["size"]].append(r)

    for size, entries in by_size.items():
        puzzles = sorted({e["puzzle"] for e in entries})
        x = list(range(len(puzzles)))

        by_solver = {}
        for e in entries:
            solver = e["solver"]
            if solver not in by_solver:
                by_solver[solver] = {}
            by_solver[solver][e["puzzle"]] = e["elapsed"]

        plt.figure()
        for solver, puzzle_map in by_solver.items():
            ys = []
            for p in puzzles:
                if p in puzzle_map:
                    ys.append(puzzle_map[p])
                else:
                    ys.append(float("nan"))
            plt.plot(x, ys, marker="o", label=solver)
        
        plt.xticks(x)
        plt.xlabel("Puzzle index")
        plt.ylabel("Runtime (s)")
        plt.title(f"Runtime per puzzle for size {size}x{size}")
        plt.legend()
        plt.tight_layout()

        out_path = os.path.join(os.path.abspath("plots"), f"runtime_n{size}.png")
        plt.savefig(out_path)
        plt.close()
        print(f"Saved {out_path}")

def _plot_puzzlestatistic(results, statistic):
    by_size = {}
    for r in results:
        size = r["size"]
        if size not in by_size:
            by_size[size] = []
        by_size[r["size"]].append(r)
    
    for size, entries in by_size.items():
        puzzles = sorted({e["puzzle"] for e in entries})
        x = list(range(len(puzzles)))

        by_solver = {}
        for e in entries:
            solver = e["solver"]
            if solver not in by_solver:
                by_solver[solver] = {}
            stat = e["statistics"].get(statistic, 0)
            by_solver[solver][e["puzzle"]] = stat

        plt.figure()
        for solver, puzzle_map in by_solver.items():
            ys = []
            for p in puzzles:
                if p in puzzle_map:
                    ys.append(puzzle_map[p])
                else:
                    ys.append(float("nan"))
            plt.plot(x, ys, marker="o", label=solver)
        
        plt.xticks(x)
        plt.xlabel("Puzzle index")
        plt.ylabel(f"{statistic.title()}")
        plt.title(f"{statistic.title()} per puzzle for size {size}x{size}")
        plt.legend()
        plt.tight_layout()

        out_path = os.path.join(os.path.abspath("plots"), f"{statistic}_n{size}.png")
        plt.savefig(out_path)
        plt.close()
        print(f"Saved {out_path}")

def _plot_puzzleconflicts(results):
    _plot_puzzlestatistic(results, "conflicts")

def _plot_puzzlepropagations(results):
    _plot_puzzlestatistic(results, "propagations")

def _plot_puzzledecisions(results):
    _plot_puzzlestatistic(results, "decisions")
    
def _plot_avgruntime(results):
    sums = {}
    counts = {}

    for r in results:
        key = (r["size"], r["solver"])
        if key not in sums:
            sums[key] = 0.0
            counts[key] = 0
        sums[key] += r["elapsed"]
        counts[key] += 1

    sizes = sorted({size for (size, _) in sums.keys()})
    solvers = sorted({solver for (_, solver) in sums.keys()})

    for size in sizes:
        avg_per_solver = []
        solver_labels = []
        for solver in solvers:
            key = (size, solver)
            if key in sums:
                avg = sums[key] / counts[key]
                avg_per_solver.append(avg)
                solver_labels.append(solver)
        
        if not avg_per_solver:
            continue

        plt.figure()
        x = list(range(len(solver_labels)))
        plt.bar(x, avg_per_solver)
        plt.xticks(x, solver_labels)
        plt.xlabel("Solver")
        plt.ylabel("Average runtime (s)")
        plt.title(f"Average runtime per solver for size {size}x{size}")
        plt.tight_layout()
        
        out_path = os.path.join(os.path.abspath("plots"), f"avg_runtime_n{size}.png")
        plt.savefig(out_path)
        plt.close()
        print(f"Saved {out_path}")

def _plot_scalingavgruntime(results):
    sums = {}
    counts = {}

    for r in results:
        key = (r["size"], r["solver"])
        if key not in sums:
            sums[key] = 0.0
            counts[key] = 0
        sums[key] += r["elapsed"]
        counts[key] += 1

    sizes = sorted({size for (size, _) in sums.keys()})
    solvers = sorted({solver for (_, solver) in sums.keys()})

    plt.figure()
    for solver in solvers:
        x_sizes = []
        y_avgs = []
        for size in sizes:
            key = (size, solver)
            if key in sums:
                avg = sums[key] / counts[key]
                x_sizes.append(size)
                y_avgs.append(avg)
        if x_sizes:
            plt.plot(x_sizes, y_avgs, marker="o", label=solver)

    plt.xlabel("Puzzle size n (n x n)")
    plt.ylabel("Average runtime (s)")
    plt.title("Average runtime by puzzle size")
    plt.legend()
    plt.tight_layout()

    out_path = os.path.join(os.path.abspath("plots"), f"scaling_avg_runtime.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")

def _plot_scalingavgstatistic(results, statistic, stat_name, plot_name, file_name):
    sums = {}
    counts = {}

    for r in results:
        key = (r["size"], r["solver"])
        if key not in sums:
            sums[key] = 0.0
            counts[key] = 0
        sums[key] += r["statistics"].get(statistic, 0)
        counts[key] += 1

    sizes = sorted({size for (size, _) in sums.keys()})
    solvers = sorted({solver for (_, solver) in sums.keys()})

    plt.figure()
    for solver in solvers:
        x_sizes = []
        y_avgs = []
        for size in sizes:
            key = (size, solver)
            if key in sums:
                avg = sums[key] / counts[key]
                x_sizes.append(size)
                y_avgs.append(avg)
        if x_sizes:
            plt.plot(x_sizes, y_avgs, marker="o", label=solver)

    plt.xlabel("Puzzle size n (n x n)")
    plt.ylabel(f"Average number of {stat_name}")
    plt.title(plot_name)
    plt.legend()
    plt.tight_layout()

    out_path = os.path.join(os.path.abspath("plots"), file_name)
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")

def _plot_scalingavgboolvars(results):
    _plot_scalingavgstatistic(results, "bool_vars", "Boolean variables", "Average encoding size by puzzle size (bool_vars)", "scaling_avg_encoding_boolvars.png")

def _plot_scalingavgclauses(results):
    _plot_scalingavgstatistic(results, "clauses", "clauses", "Average encoding size by puzzle size (clauses)", "scaling_avg_encoding_clauses.png")

def _plot_scalingavgbinclauses(results):
    _plot_scalingavgstatistic(results, "bin_clauses", "binary clauses", "Average encoding size by puzzle size (bin_clauses)", "scaling_avg_encoding_binclauses.png")

PLOT_TYPES = {
    1: {
        "f": _plot_puzzleruntime,
        "description": "Runtime vs puzzle (per size, line plot, one line per solver)",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    2: {
        "f": _plot_puzzleconflicts,
        "description": "Conflict vs puzzle (per size, line plot, one line per solver)",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    3: {
        "f": _plot_puzzledecisions,
        "description": "Decisions vs puzzle (per size, line plot, one line per solver)",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    4: {
        "f": _plot_puzzlepropagations,
        "description": "Propagations vs puzzle (per size, line plot, one line per solver)",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    5: {
        "f": _plot_avgruntime,
        "description": "Average runtime per solver and size (bar chart)",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    6: {
        "f": _plot_scalingavgruntime,
        "description": "Average runtime by puzzle size",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    7: {
        "f": _plot_scalingavgboolvars,
        "description": "Average Boolean variables by puzzle size",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    8: {
        "f": _plot_scalingavgclauses,
        "description": "Average clauses by puzzle size",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    },
    9: {
        "f": _plot_scalingavgbinclauses,
        "description": "Average binary clauses by puzzle size",
        "requires": {
            "min_puzzles": 1,
            "min_solvers": 1
        }
    }
}

def plot(id: int, results: list[dict]) -> None:
    if id not in PLOT_TYPES:
        print(f"Unknown plot id {id}")
        return
    
    meta = PLOT_TYPES[id]
    f = meta["f"]
    req = meta["requires"]

    puzzle_set = {r["puzzle"] for r in results}
    solver_set = {r["solver"] for r in results}

    min_puzzles = req.get("min_puzzles", 1)
    min_solvers = req.get("min_solvers", 1)
    if len(puzzle_set) < min_puzzles:
        print(f"Plot {id} requires at least {min_puzzles} puzzle(s)")
        return
    if len(solver_set) < min_solvers:
        print(f"Plot {id} requires at least {min_solvers} solver(s)")
        return
    
    os.makedirs(os.path.abspath("plots"), exist_ok=True)
    print(f"Generating plot {id}: {meta['description']}")
    f(results)