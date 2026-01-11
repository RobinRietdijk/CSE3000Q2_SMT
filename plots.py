import os
import matplotlib.pyplot as plt
import scienceplots
import scipy
import numpy as np

plt.style.use(['science','ieee'])

plt.rcParams.update({
    "lines.linewidth": 0.8,
    "lines.markersize": 1,
    "legend.fontsize": 6,
    "legend.title_fontsize": 5,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "xtick.minor.visible": False,
    "axes.grid.which": "major",
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "ytick.minor.size": 1.5,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "ytick.minor.width": 0.5,
    "xtick.top": False,
    "ytick.right": False,
    "xtick.bottom": True,
    "ytick.left": True,
    "axes.grid": True,
    "axes.grid.which": "major",
    "grid.color": "0.85",
    "grid.alpha": 0.6,
    "grid.linewidth": 0.6,
    "grid.linestyle": "-", 
})

plt.rcParams["axes.prop_cycle"] = plt.cycler(color=[ # type: ignore
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#a6cee3", "#fb9a99", "#fdbf6f", "#b2df8a", "#cab2d6",
    "#ffff99", "#33a02c", "#b15928", "#e31a1c", "#1f78b4"
])

LINE_STYLES = ["-", "--", "-.", ":"]

def _log_differences(results: list, statistic, solver1: str, solver2: str, size: int) -> list:
    a = {}
    b = {}

    for r in results:
        if r["size"] == size:
            if r["solver"] == solver1:
                a[r["puzzle"]] = r["statistics"][statistic]
            elif r["solver"] == solver2:
                b[r["puzzle"]] = r["statistics"][statistic]

    common = sorted(set(a) & set(b))
    differences = [a[puzzle]-b[puzzle] for puzzle in common]
    return differences

def plot_qq(results: list, statistic, solver1: str, solver2: str, size: int) -> None:
    differences = _log_differences(results, statistic, solver1, solver2, size)

    scipy.stats.probplot(differences, plot=plt)
    plt.title("Q–Q plot of paired log-runtime differences")
    plt.show()
