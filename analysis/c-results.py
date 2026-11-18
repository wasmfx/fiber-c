#!/usr/bin/env python3

import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict


ENGINES = ["d8", "wasmtime", "wizard"]
STYLES = ["asyncify", "wasmfx"]

# Publication-friendly defaults
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def load_data(filenames):
    results = []

    for filename in filenames:
        with open(filename) as f:
            data = json.load(f)
            results.extend(data["results"])

    # benchmarks = sorted({
    #     r["parameters"]["benchmark"] for r in results
    # })
    benchmarks = ['itersum', 'c10m', 'pi', 'treesum']
    print(f"Found {len(benchmarks)} benchmarks: {benchmarks}")

    lookup = {}

    for r in results:
        p = r["parameters"]
        key = (p["engine"], p["style"], p["benchmark"])

        lookup[key] = {
            "median": r["median"],
            "min": r["min"],
            "max": r["max"],
        }

    return benchmarks, lookup


def plot(filenames, output):
    benchmarks, lookup = load_data(filenames)

    fig, ax = plt.subplots(figsize=(9, 3.5))

    # Colors distinguish engines
    colors = {
        engine: color
        for engine, color in zip(
            ENGINES,
            plt.cm.Set2(np.linspace(0, 1, len(ENGINES)))
        )
    }

    bar_width = 0.11
    style_gap = 0.035
    engine_gap = 0.20

    x = 0
    benchmark_positions = defaultdict(list)

    # for engine in ENGINES:
    for benchmark in benchmarks:
        for engine in ENGINES:
        # for benchmark in benchmarks:
            for style in STYLES:
                key = (engine, style, benchmark)

                if (key == ("wizard", "asyncify", "c10m")):
                    ax.text(
                        x,
                        0.02,                  # Vertical position
                        "N/A",
                        ha="center",
                        va="bottom",
                        fontsize=10,
                        color="black",
                        transform=ax.get_xaxis_transform(),
                    )
                    x += bar_width
                    continue

                result = lookup[key]

                median = result["median"]
                lower = median - result["min"]
                upper = result["max"] - median

                ax.bar(
                    x,
                    median,
                    width=bar_width,
                    color=colors[engine],
                    edgecolor="black",
                    linewidth=0.4,
                    hatch="//" if style == "asyncify" else None,
                    zorder=3,
                )

                ax.errorbar(
                    x,
                    median,
                    yerr=[[lower], [upper]],
                    fmt="none",
                    ecolor="black",
                    capsize=2,
                    linewidth=0.8,
                    zorder=4,
                )

                benchmark_positions[benchmark].append(x)
                x += bar_width

            x += style_gap

        x += engine_gap

    # Benchmark labels repeated for each engine/style combination
    # Individual benchmark positions are centered below their bars.
    ax.set_xticks([])

    # Add hierarchical labels
    for benchmark in benchmarks:
        positions = benchmark_positions[benchmark]
        if not positions:
            print(f"Warning: No positions found for benchmark '{benchmark}'")
            continue

        center = (positions[0] + positions[-1]) / 2

        name = benchmark

        ax.text(
            center, -0.12, name,
            ha="center", va="top",
            transform=ax.get_xaxis_transform(),
            fontweight="bold"
        )

    # Legend: engine colors and style hatches
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(
            facecolor=colors[b],
            edgecolor="black",
            label="v8" if b == "d8" else b
        )
        for b in ENGINES
    ]

    legend_elements += [
        Patch(facecolor="white", edgecolor="black",
            hatch="//", label="asyncify"),
        Patch(facecolor="white", edgecolor="black",
            label="wasmfx"),
    ]

    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.20),
        ncol=len(legend_elements),
        frameon=False,
    )

    ax.set_ylabel("Runtime (seconds)")
    ax.set_xlim(-bar_width, x - engine_gap)
    ax.grid(axis="y", linestyle=":", alpha=0.5, zorder=0)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        top=0.78,
        bottom=0.25
    )

    fig.savefig(output + ".pdf", bbox_inches="tight")
    fig.savefig(output + ".png", dpi=300, bbox_inches="tight")

    print(f"Saved {output}.pdf and {output}.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input JSON files"
    )
    parser.add_argument(
        "-o", "--output",
        default="benchmark-results",
        help="Output filename (without extension)"
    )

    args = parser.parse_args()
    plot(args.inputs, args.output)