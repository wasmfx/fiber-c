#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "matplotlib",
#     "pyqt6",
#     "numpy",
# ]
# ///
"""
Script that generates:
    1. A bar chart displaying the relative performance of asyncify and wasmfx benchmarks, grouped by engine
    2. $number_of_engines$ bar charts displaying the raw runtime/binary size/etc data for each engine
    3. $number_of_benchmarks$ bar charts displaying the raw runtime/binary size/etc data for each benchmark

Where
    (1) is saved in results_dir/relative/relative.png,
    (2) is saved in results_dir/absolute_engines/absolute_{engine}.png,
    (3) is saved in results_dir/absolute_benchmarks/absolute_{benchmark}.png

Usage:
    `python3 plot_benchmarks.py results_wasmfx.json results_asyncify.json --benchmarks itersum --engines wasmtime d8 -o results_dir`
"""

import argparse
import json
import os
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import math

# deal with inputs
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "files", nargs="+", type=pathlib.Path, help="JSON files with benchmark results"
)
parser.add_argument(
    "--benchmarks",
    nargs="*",
    help="List of benchmarks to plot (e.g. sieve, itersum, treesum)",
)
parser.add_argument(
    "--engines", nargs="*", help="List of engines to plot (d8, wasmtime, wizard)"
)
parser.add_argument(
    "-o",
    "--output",
    help="""
    Save image to the given directory (specific charts will be saved in subdirectories
    relative/, absolute_engines/, and absolute_benchmarks/)
    """,
)

args = parser.parse_args()
benches = args.benchmarks
engines = args.engines
styles = ["wasmfx", "asyncify"]

if benches is None:
    raise ValueError("--benchmarks of interest must be specified")

if engines is None:
    raise ValueError("--engines of interest must be specified")

# Load a set of files, either by directory or as an immediate list of files.
if os.path.isdir(args.files[0]):
    if len(args.files) > 1:
        raise ValueError(
            "files input should be a single dir with all benchmark results, or a list of json files."
        )

    files = pathlib.Path(args.files[0]).glob("results_*.json")
else:
    files = args.files

# Collect all the JSON data into a list of results we can query.
data = []
for i, filename in enumerate(files):
    print(f"Loading data from {filename}...")
    with open(filename) as f:
        data.extend(json.load(f)["results"])


# Predicates for the hyperfine output json format, to filter results by
# benchmark, engine, and style (wasmfx vs asyncify).
def benchmark_is(result, benchmark):
    return result["parameters"]["benchmark"] == benchmark


def engine_is(result, engine):
    return result["parameters"]["engine"] == engine


def style_is(result, style):
    return result["parameters"]["style"] == style


def fetch_one(data, style, benchmark, engine):
    return [
        x
        for x in data
        if style_is(x, style) and benchmark_is(x, benchmark) and engine_is(x, engine)
    ][0]


def organize(data):
    """Organize the data into a 3-level nested list, by style, benchmark, engine, in the order
    specified by the global lists `benches` and `engines`. If there are extra data points in the
    input, they are dropped. If any of the specified combinations is missing, we'll get an
    IndexError.
    """
    return [
        [
            [fetch_one(data, style, benchmark, engine) for engine in engines]
            for benchmark in benches
        ]
        for style in styles
    ]


def grouped_position(set, offset, cadence):
    """Maps an item in a grouped set of sets to a unique x value for plotting, given the offset of
    the set and the cadence (number of items in each set).
    """
    return set * (cadence + 1) + offset


def array_positions(ary):
    """Returns positions for items in a grouped list-of-lists, with gaps between groups.

    Outermost indices correspond to ary's outer indices, and inner to inner.
    """
    return [
        [grouped_position(j, i, len(ary)) for j in range(len(ary[0]))]
        for i in range(len(ary))
    ]


nested_data = organize(data)
data_means = np.array(
    [[[cell["mean"] for cell in row] for row in plane] for plane in nested_data]
)
data_stddev = np.array(
    [[[cell["stddev"] for cell in row] for row in plane] for plane in nested_data]
)
# We now have two numpy arrays whose dimensions are [style][benchmark][engine]

ASYNCIFY_INDEX = 1
WASMFX_INDEX = 0

# The width of the bars in the chart
width = 1
# Hope this is colourblind-friendly enough for sam
bar_colors = [
    "tab:blue",
    "tab:orange",
    "tab:cyan",
    "tab:red",
    "tab:purple",
    "tab:brown",
    "tab:pink",
    "tab:gray",
]

# --------------
# ------- First chart: ratio of asyncify time to wasmfx time for each benchmark across all engines -----
# --------------

data_wasmfx_means = data_means[WASMFX_INDEX]
data_asyncify_means = data_means[ASYNCIFY_INDEX]

# Get the chart data: divide first column by second column to obtain asyncify / wasmfx ratio
ratio = np.divide(data_asyncify_means, data_wasmfx_means)

# Get the standard deviation for the ratio.
# First we want the standard deviations as percentages of the mean:
data_wasmfx_stddev = data_stddev[WASMFX_INDEX]
data_asyncify_stddev = data_stddev[ASYNCIFY_INDEX]
# Then we apply the formula for error propagation for division
ratio_stddev = ratio * np.sqrt(
    np.square(data_asyncify_stddev / data_asyncify_means)
    + np.square(data_wasmfx_stddev / data_wasmfx_means)
)

# Compute x values for bar locations, with gaps between groups of bars for each engine
#   eg. x = [0,1,2,4,5,6,8,9,10] for 3 benchmarks across 3 engines,
#   with a gap of 1 between each group of 3 bars for each engine
bar_loc = array_positions(ratio)

# Plot the data
fig, ax = plt.subplots()

for i in range(len(ratio)):
    ax.bar(
        bar_loc[i],
        ratio[i],
        width,
        label=benches[i],
        color=bar_colors[i],
    )

# Pad out list of engines to match number of benchmarks, so x-axis labels are engines
axis_labels = np.repeat(engines, len(benches))
ax.set_xticks(np.array(bar_loc).transpose().flatten(), axis_labels)

# Keeps every nth label, make the rest invisible
n = len(benches)
[
    l.set_visible(False)
    for (i, l) in enumerate(ax.xaxis.get_ticklabels())
    if i % n != math.ceil(n / 2) - 1
]

# Error bars
plt.errorbar(
    np.array(bar_loc).flatten(),
    ratio.flatten(),
    yerr=ratio_stddev.flatten(),
    fmt="none",
    capsize=3,
    linewidth=0.5,
    color="black",
    label="Standard Deviation",
)

# Readability features
ax.grid(visible=True, axis="y")
plt.title("Benchmark results (Asyncify time / WasmFX time)")
plt.xlabel("Engine")
plt.ylabel("Speedup (relative to Asyncify)")
plt.legend(benches, bbox_to_anchor=(1.3, 1), loc="upper right")

# Add a horizontal line at y=1 to indicate where wasmfx and asyncify have equal performance
plt.axhline(y=1.0, color="r", linestyle="--", linewidth=3, label="WasmFX = Asyncify")

# Export figure
if args.output:
    plt.savefig(f"{args.output}/relative/relative", bbox_inches="tight")
else:
    plt.show()

# --------------
# ----- Next charts: absolute times for asyncify and wasmfx for each benchmark, grouped by engine -----
# --------------

# We want a different chart for each engine where bars are grouped by benchmarks,
# and each bar corresponds to a different backend (wasmfx, asyncify).
for i, engine in enumerate(engines):
    # Get array of data from this engine
    engine_data = data_means[:, :, i]
    engine_data_stddev = data_stddev[:, :, i]

    bar_loc = array_positions(engine_data)

    # Plot data
    fig, ax = plt.subplots()
    for j in range(len(styles)):
        ax.bar(
            bar_loc[j],
            engine_data[j],
            width,
            label=["WasmFX", "Asyncify"][j],
            color=bar_colors[j % 2],
        )

    # Pad out list of engines to match number of benchmarks, so x-axis labels are engines
    axis_labels = np.repeat(benches, 2)
    ax.set_xticks(np.array(bar_loc).transpose().flatten(), axis_labels)

    # Keeps every other label, make the rest invisible
    [
        l.set_visible(False)
        for (i, l) in enumerate(ax.xaxis.get_ticklabels())
        if (i + 1) % 2 == 0
    ]

    # Error bars
    plt.errorbar(
        np.array(bar_loc).flatten(),
        engine_data.flatten(),
        yerr=engine_data_stddev.flatten(),
        fmt="none",
        capsize=3,
        linewidth=0.5,
        color="black",
        label="Standard Deviation",
    )

    # Readability features
    ax.grid(visible=True, axis="y")
    plt.title(f"Benchmark results (absolute times) for {engine}")
    plt.xlabel("Benchmark")
    plt.ylabel("Time (seconds)")
    plt.legend(["WasmFX", "Asyncify"], bbox_to_anchor=(1.3, 1), loc="upper right")

    # Export figure
    if args.output:
        plt.savefig(
            f"{args.output}/absolute_engines/absolute_{engine}", bbox_inches="tight"
        )
    else:
        plt.show()

# --------------
# ----- Next charts: absolute times for asyncify and wasmfx, grouped by benchmark -----
# --------------

# Now we want a different chart for each benchmark where bars are grouped by engines
for i, benchmark in enumerate(benches):
    # Get array of data from this benchmark
    # There should always be 2 * len(engines) entries for each benchmark
    bench_data = data_means[:, i]
    bench_data_stddev = data_stddev[:, i]

    bar_loc = array_positions(bench_data)

    # Plot data
    fig, ax = plt.subplots()
    for i in range(len(bench_data)):
        ax.bar(
            bar_loc[i],
            bench_data[i],
            width,
            label=engines[i % len(engines)],
            color=bar_colors[i % 2],
        )

    # Pad out list of benchmarks to match number of engines
    axis_labels = np.repeat(engines, 2)
    ax.set_xticks(np.array(bar_loc).transpose().flatten(), axis_labels)

    # Keeps every other label, make the rest invisible
    n = len(engines)
    [
        l.set_visible(False)
        for (i, l) in enumerate(ax.xaxis.get_ticklabels())
        if (i + 1) % 2 == 0
    ]

    # Error bars
    plt.errorbar(
        np.array(bar_loc).flatten(),
        bench_data.flatten(),
        yerr=bench_data_stddev.flatten(),
        fmt="none",
        capsize=3,
        linewidth=0.5,
        color="black",
        label="Standard Deviation",
    )

    # Readability features
    ax.grid(visible=True, axis="y")
    plt.title(f"Benchmark results (absolute times) for {benchmark}")
    plt.xlabel("Engine")
    plt.ylabel("Time (seconds)")
    plt.legend(["WasmFX", "Asyncify"], bbox_to_anchor=(1.3, 1), loc="upper right")

    # Export figure
    if args.output:
        plt.savefig(
            f"{args.output}/absolute_benchmarks/absolute_{benchmark}",
            bbox_inches="tight",
        )
    else:
        plt.show()
