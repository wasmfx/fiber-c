#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

# STYLES = ["wasmtime_wasmfx", "wasmfx", "reified"]
STYLES = ["wasmfx", "reified"]

def load_results(paths):
    results = []
    for path in paths:
        with open(path, "r") as f:
            results.extend(json.load(f)["results"])
    return results


def plot_results(results):
    # Organize results by benchmark and style
    grouped = defaultdict(dict)

    for result in results:
        params = result["parameters"]
        benchmark = params["benchmark"]
        style = params["style"]

        grouped[benchmark][style] = result

    benchmarks = sorted(grouped.keys())
    x = np.arange(len(benchmarks))
    width = 0.8 / len(STYLES)

    fig, ax = plt.subplots(figsize=(max(9, len(benchmarks) * 1.5), 6))

    colors = {
        "reified": "#4C78A8",
        "wasmfx": "#F58518",
        "wasmtime_wasmfx": "#54A24B",
    }

    for i, style in enumerate(STYLES):
        means = []
        stddevs = []

        for benchmark in benchmarks:
            result = grouped[benchmark].get(style)

            if result is None:
                means.append(np.nan)
                stddevs.append(0)
            else:
                means.append(result["mean"])
                stddevs.append(result.get("stddev", 0))

        positions = x + (i - (len(STYLES) - 1) / 2) * width

        ax.bar(
            positions,
            means,
            width,
            yerr=stddevs,
            capsize=4,
            label=style,
            color=colors[style],
            edgecolor="black",
            linewidth=0.5,
        )

    ax.set_xlabel("Benchmark")
    ax.set_ylabel("Execution time (seconds)")
    ax.set_title("Benchmark performance on V8-wasmfx and V8-reified-fibers")
    ax.set_xticks(x)
    ax.set_xticklabels(benchmarks, rotation=30, ha="right")
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    plt.savefig("reified_results/reified_benchmark_results.png", dpi=200, bbox_inches="tight")
    plt.show()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} result1.json [result2.json ...]")
        sys.exit(1)

    results = load_results(sys.argv[1:])
    plot_results(results)


if __name__ == "__main__":
    main()
