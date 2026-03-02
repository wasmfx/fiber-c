#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "matplotlib",
#     "pyqt6",
#     "numpy",
# ]
# ///

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
parser.add_argument(
    "files", nargs="+", type=pathlib.Path, help="JSON files with benchmark results"
)
parser.add_argument(
        "-benchmarks", "--benchmarks", nargs="*", help="List of benchmarks to run (sieve, itersum, treesum)", 
        default=config["BENCHMARKS"]
    )
parser.add_argument(
        "-engines", "--engines", nargs="*", help="List of engines to run (d8, wasmtime, wizard)", 
        default=config["ENGINES"]
    )
parser.add_argument("-o", "--output", help="Save image to the given filename")

args = parser.parse_args()

commands = None
data = []
inputs = []

for i, filename in enumerate(args.files):
    with open(filename) as f:
        results = json.load(f)["results"]
    benchmark_commands = [b["command"] for b in results]
    if commands is None:
        commands = benchmark_commands
    data.append([round(b["mean"], 6) for b in results])
    inputs.append(filename.stem)

data = np.transpose(data)

# divide first column by second column to obtain wasmfx / asyncify ratio 
# for each benchmark across all engines
ratio = np.divide(data[:, 1], data[:, 0])

benches = args.benchmarks
engines = args.engines

# x values for bar locations, with gaps between groups of bars for each engine#
#   eg. x = [0,1,2,4,5,6,8,9,10] for 3 benchmarks across 3 engines, 
#   with a gap of 1 between each group of 3 bars for each engine
x = [x for x in np.arange((len(benches) + 1) * len(engines)) if ((x+1) % (len(benches) + 1)) != 0]

# the width of the bars
width = 1
bar_colors = ['tab:blue', 'tab:orange', 'tab:cyan', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray']

fig, ax = plt.subplots()

for i in range(len(ratio)):
    ax.bar(x[i], ratio[i], width, label=benches[i % len(benches)], color=bar_colors[i % len(benches)])

# pad out list of engines to match length of commands, so x-axis labels are engines
axis_labels = np.repeat(engines, len(benches))
ax.set_xticks(x, axis_labels)

# Keeps every nth label, make the rest invisible
n = len(benches)
[l.set_visible(False) for (i,l) in enumerate(ax.xaxis.get_ticklabels()) if i % n != math.ceil(n/2) - 1]

ax.grid(visible=True, axis="y")
plt.title("Benchmark results (Asyncify time / WasmFX time)")
plt.xlabel("Engine")
plt.ylabel("Time [s]")
# plt.ylim(0, 1.2)
plt.legend(benches, bbox_to_anchor=(1.3, 1), loc="upper right")


if args.output:
    plt.savefig(f"bench_results/{args.output}", bbox_inches="tight")
else:
    plt.show()