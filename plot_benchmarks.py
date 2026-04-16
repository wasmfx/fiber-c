#!/usr/bin/env python
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
Usage: 
    `python3 plot_benchmarks.py results_wasmfx.json results_asyncify.json --benchmarks itersum --engines wasmtime d8 -o results_dir`
    `todo: sample usage for making charts of binary sizes`
"""
import argparse
import json
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import yaml
import math

config = yaml.safe_load(open("config.yml"))

# deal with inputs
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("files", nargs="+", type=pathlib.Path, help="JSON files with benchmark results")
parser.add_argument("--benchmarks", nargs="*", help="List of benchmarks to run (sieve, itersum, treesum)")
parser.add_argument("--engines", nargs="*", help="List of engines to run (d8, wasmtime, wizard)")
parser.add_argument("-o", "--output", help="Save image to the given filename")

args = parser.parse_args()
benches = args.benchmarks
engines = args.engines

# Parse JSON files to extract benchmark results, we are only interested in the mean times
data = []
inputs = []

# Make an array where each row corresponds to a benchmark/engine pair, each column corresponds to a backend (wasmfx vs asyncify), 
# and the values are the mean runtimes from the hyperfine output json file
for i, filename in enumerate(args.files):
    with open(filename) as f:
        results = json.load(f)["results"]
    data.append([round(b["mean"], 6) for b in results])
    inputs.append(filename.stem)

data = np.transpose(data)

# The width of the bars in the chart
width = 1
# Hope this is colourblind-friendly enough for sam
bar_colors = ['tab:blue', 'tab:orange', 'tab:cyan', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray']

# --------------
# ------- First chart: ratio of asyncify time to wasmfx time for each benchmark across all engines -----
# --------------

# Get the chart data: divide first column by second column to obtain wasmfx / asyncify ratio
ratio = np.divide(data[:, 1], data[:, 0])

# Compute x values for bar locations, with gaps between groups of bars for each engine
#   eg. x = [0,1,2,4,5,6,8,9,10] for 3 benchmarks across 3 engines, 
#   with a gap of 1 between each group of 3 bars for each engine
bar_loc = [x for x in np.arange((len(benches) + 1) * len(engines)) if ((x+1) % (len(benches) + 1)) != 0]

# Plot the data
fig, ax = plt.subplots()
for i in range(len(ratio)):
    ax.bar(bar_loc[i], ratio[i], width, label=benches[i % len(benches)], color=bar_colors[i % len(benches)])

# Pad out list of engines to match number of benchmarks, so x-axis labels are engines
axis_labels = np.repeat(engines, len(benches))
ax.set_xticks(bar_loc, axis_labels)

# Keeps every nth label, make the rest invisible
n = len(benches)
[l.set_visible(False) for (i,l) in enumerate(ax.xaxis.get_ticklabels()) if i % n != math.ceil(n/2) - 1]

# Readability features
ax.grid(visible=True, axis="y")
plt.title("Benchmark results (Asyncify time / WasmFX time)")
plt.xlabel("Engine")
plt.ylabel("Speedup (relative to Asyncify)")
plt.legend(benches, bbox_to_anchor=(1.3, 1), loc="upper right")

# Add a horizontal line at y=1 to indicate where wasmfx and asyncify have equal performance
plt.axhline(
    y=1.0, 
    color = 'r',
    linestyle = '--', 
    linewidth = 3,
    label = 'WasmFX = Asyncify'
    )

# Export figure
if args.output:
    plt.savefig(f"{args.output}_relative", bbox_inches="tight")
else:
    plt.show()

# --------------
# ----- Next 3 (or rather, len(engines)) charts: absolute times for asyncify and wasmfx for each benchmark, per engine -----
# --------------

# We want a different chart for each engine where bars are grouped by benchmarks, 
# and each bar corresponds to a different backend (wasmfx, asyncify).
for i, engine in enumerate(engines):
    # Get array of data from this engine
    engine_data = data[(i)*(len(benches)):(i+1)*(len(benches))].flatten()

    # Set x values for bar locations, with one group of (two) bars for each benchmark
    bar_loc = [x for x in np.arange((len(benches) + 1) * 2) if ((x+1) % 3) != 0]

    # Plot data
    fig, ax = plt.subplots()
    for i in range(len(engine_data)):
        ax.bar(bar_loc[i], engine_data[i], width, label=benches[i % len(benches)], color=bar_colors[i % 2])

    # Pad out list of engines to match number of benchmarks, so x-axis labels are engines
    axis_labels = np.repeat(benches, 2)
    ax.set_xticks(bar_loc, axis_labels)

    # Keeps every other label, make the rest invisible
    n = len(benches)
    [l.set_visible(False) for (i,l) in enumerate(ax.xaxis.get_ticklabels()) if (i+1) % 2 == 0]

    # Readability features
    ax.grid(visible=True, axis="y")
    plt.title(f"Benchmark results (absolute times) for {engine}")
    plt.xlabel("Benchmark")
    plt.ylabel("Time (milliseconds)")
    plt.legend(['WasmFX', 'Asyncify'], bbox_to_anchor=(1.3, 1), loc="upper right")

    # Export figure
    if args.output:
        plt.savefig(f"{args.output}_{engine}_absolute", bbox_inches="tight")
    else:
        plt.show()

# todo: binary sizes chart