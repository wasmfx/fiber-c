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
Script that generates a chart comparing the binary sizes of asyncify and wasmfx benchmarks.
Usage: 
    `python3 plot_binary_sizes.py results_binary_sizes.json --benchmarks itersum -o results_dir`
"""

import argparse
import json
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import math

# deal with inputs
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--benchmarks", nargs="*", help="List of benchmarks to run (sieve, itersum, treesum)")
parser.add_argument("files", type=pathlib.Path, help="JSON files with binary sizes")
parser.add_argument("-o", "--output", help="Save image to the given filename")

args = parser.parse_args()
benches = args.benchmarks

with open(args.files) as f:
    data = json.load(f)

data = np.array(data)

# Get the chart data: divide first column by second column to obtain wasmfx / asyncify ratio
ratio = np.divide(data[:, 1], data[:, 0])

# The width of the bars in the chart
width = 1

# Hope this is colourblind-friendly enough for sam
bar_colors = ['tab:blue', 'tab:orange', 'tab:cyan', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray']

# x-values for bar locations
bar_loc = np.arange(len(benches))

# Plot the data
fig, ax = plt.subplots()
for i in range(len(ratio)):
    ax.bar(bar_loc[i], ratio[i], width, label=benches[i], color=bar_colors[i])

ax.set_xticks(bar_loc, benches)
ax.grid(visible=True, axis="y")
plt.title(f"Benchmark binary size comparison (Asyncify size / WasmFX size)")
plt.xlabel("Benchmark")
plt.ylabel("Size Ratio")
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
    plt.savefig(f"{args.output}_relative_binary_sizes", bbox_inches="tight")
else:
    plt.show()
