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
Script that plots the results of the treesum benchmark when ran with different arguments.
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
    "-o",
    "--output",
    help="""
    Save image to the given directory (specific charts will be saved in subdirectories
    relative/, absolute_engines/, and absolute_benchmarks/)
    """,
)

args = parser.parse_args()
styles = ["wasmfx", "asyncify"]

# Load a set of files, either by directory or as an immediate list of files.
if os.path.isdir(args.files[0]):
    if len(args.files) > 1:
        raise ValueError(
            "files input should be a single dir with all benchmark results, or a list of json files."
        )

    results_files = pathlib.Path(args.files[0]).glob("*.json")

# Collect all the JSON data into a list of results we can query.
data = []
for i, filename in enumerate(results_files):
    print(f"Loading data from {filename}...")
    with open(filename) as f:
        data.extend(json.load(f)["results"])

# Predicates for the hyperfine output json format, to filter results by
# benchmark, engine, and style (wasmfx vs asyncify).
def style_is(result, style):
    return result["parameters"]["style"] == style

results_wasmfx = [x for x in data if style_is(x, "wasmfx")]
results_asyncify = [x for x in data if style_is(x, "asyncify")]

args_wasmfx = [x["parameters"]["arg"] for x in results_wasmfx]
args_asyncify = [x["parameters"]["arg"] for x in results_asyncify]

# TODO: this script only plots data from one engine so let's be lazy here
engine = results_wasmfx[0]["parameters"]["engine"]

data_means_wasmfx = np.array(
    [cell["mean"] for cell in results_wasmfx]
)
data_means_asyncify = np.array(
    [cell["mean"] for cell in results_asyncify]
)
data_stddev_wasmfx = np.array(
    [cell["stddev"] for cell in results_wasmfx]
)
data_stddev_asyncify = np.array(
    [cell["stddev"] for cell in results_asyncify]
)

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


plt.plot(args_wasmfx, data_means_wasmfx, label ='wasmfx')
plt.plot(args_asyncify, data_means_asyncify, '-.', label ='asyncify')

plt.xlabel("Argument")
plt.ylabel("Runtime (seconds)")
plt.legend()
plt.title(f'Treesum performance on {engine}')


# Export figure
if args.output:
    plt.savefig(
        f"{args.output}/treesum_comparison", bbox_inches="tight"
    )
else:
    plt.show()