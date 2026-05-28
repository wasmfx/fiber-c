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
Script that generates a bar chart displaying the relative performance of switch/non-switch benchmarks for each engine

Usage: 
    `python3 plot_benchmarks.py results_wasmfx.json --benchmarks itersum --engines wasmtime d8 -o results_dir`
"""

import argparse
import json
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import math

# deal with inputs
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("files", type=pathlib.Path, help="JSON file with benchmark results")
parser.add_argument("--benchmarks", nargs="*", help="List of benchmarks to run (sieve, itersum, treesum)")
parser.add_argument("--engines", nargs="*", help="List of engines to run (d8, wasmtime, wizard)")
parser.add_argument("-o", "--output", help="Save image to the given filename")

args = parser.parse_args()
benches = args.benchmarks
engines = args.engines

# Parse JSON files to extract benchmark results, we are only interested in the mean times
data = []
data_stddev = []

# Make an array where each row corresponds to a benchmark/engine pair, each column corresponds to a backend (switch vs non-switch), 
# and the values are the mean runtimes from the hyperfine output json file
with open(args.files) as f:
    results = json.load(f)["results"]
data.append([round(b["mean"], 6) for b in results])
data_stddev.append([round(b["stddev"], 6) for b in results])

# Unpack data from list of lists
data = data[0]
data_stddev = data_stddev[0]

# The width of the bars in the chart
width = 1
# Hope this is colourblind-friendly enough for sam
bar_colors = ['tab:blue', 'tab:orange', 'tab:cyan', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray']

# --------------
# ----- Absolute times for switch and non-switch for each benchmark, one chart per engine -----
# --------------

for i, engine in enumerate(engines):
    # The data varies parameters in the order: benchmark -> switch -> engine
    # Therefore, data for each engine is obtained by:
    engine_data = [data[j] for j in range(i * len(benches), (i+1) * len(benches))]
    engine_data_stddev = [data_stddev[j] for j in range(i * len(benches), (i+1) * len(benches))]

    # Set x values for bar locations, with one group of (two) bars for each switch/non-switch pair
    # Logic: for each benchmark we allocate three bars, where the third one is a gap, so we don't 
    # have multiples of 3 in our list of x-values. 
    bar_loc = [x for x in np.arange((len(benches) / 2) * 3) if ((x+1) % 3) != 0]

    # Plot data
    fig, ax = plt.subplots()
    for i in range(len(engine_data)):
        ax.bar(bar_loc[i], engine_data[i], width, label=benches[i % len(benches)], color=bar_colors[i % 2])

    # Set x-axis labels to be benchmark names, with one label per switch/non-switch pair
    axis_labels = np.repeat([benches[i] for i in range(len(benches)) if i % 2 == 1] , 2)
    ax.set_xticks([x + 0.5 for x in bar_loc], axis_labels)

    # Keeps every other label, make the rest invisible
    [l.set_visible(False) for (i,l) in enumerate(ax.xaxis.get_ticklabels()) if (i+1) % 2 == 0]

    # Error bars
    plt.errorbar(bar_loc, engine_data, yerr=engine_data_stddev, fmt='.', color='black', label='Standard Deviation')

    # Readability features
    ax.grid(visible=True, axis="y")
    plt.title(f"Switch benchmark results (absolute times) for {engine}")
    plt.xlabel("Benchmark")
    plt.ylabel("Time (seconds)")
    plt.legend(['Switch', 'Non-switch'], bbox_to_anchor=(1.3, 1), loc="upper right")

    # Export figure
    if args.output:
        plt.savefig(f"{args.output}/switch_{engine}", bbox_inches="tight")
    else:
        plt.show()
