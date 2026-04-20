#!/usr/bin/env python3
"""
Script that calls buildscript and runs fiber-c benchmarks.
Usage:  `./bench.py --help`
        `./bench.py` # runs all benchmarks on all engines by default
        `./bench.py --benchmarks sieve1 itersum --engines d8 wasmtime -o results_dir` 
            # runs selected benchmarks and engines, saves results to `bench_results/results_dir`
"""
import argparse
import yaml
import sys
import os
import subprocess
import shutil
import json
from pathlib import Path

config = yaml.safe_load(open("config.yml"))

all_benchmarks = config["BENCHMARKS_FIBER_C"]
all_engines = config["ENGINES"]

def call_buildscript():
    subprocess.check_call(["./build.py"])
    
def run_benchmarks(benchmarks, engines, filename, path):
    # call hyperfine to run wasmfx benchmarks
    subprocess.check_call(["hyperfine", "--warmup", "3", "--runs", "10", "--export-json", f"bench_results/{path}/{filename}_wasmfx.json", "--export-csv", f"bench_results/{path}/{filename}_wasmfx.csv", "-L", "benchmark", ",".join(benchmarks), "-L", "engine", ",".join(engines), "run-scripts/./{benchmark}_{engine}_wasmfx.sh"])
    # and now asyncify benchmarks
    subprocess.check_call(["hyperfine", "--warmup", "3", "--runs", "10", "--export-json", f"bench_results/{path}/{filename}_asyncify.json", "--export-csv", f"bench_results/{path}/{filename}_asyncify.csv", "-L", "benchmark", ",".join(benchmarks), "-L", "engine", ",".join(engines), "run-scripts/./{benchmark}_{engine}_asyncify.sh"])

def get_binary_sizes(benchmarks,filename, path):
    data=[]
    for benchmark in benchmarks:
        wasmfx_size = os.path.getsize(f"out/{benchmark}_wasmfx.wasm")
        asyncify_size = os.path.getsize(f"out/{benchmark}_asyncify.wasm")
        entry = {
            "benchmark": benchmark,
            "wasmfx": wasmfx_size,
            "asyncify": asyncify_size,
            }
        data.append(entry)
    with open(f"bench_results/{path}/{filename}.json", "w") as f:
        json.dump(data,f)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmarks", nargs="*", help="List of benchmarks to run (sieve, itersum, treesum)", 
        default=all_benchmarks
    )
    parser.add_argument(
        "--engines", nargs="*", help="List of engines to run (d8, wasmtime, wizard)", 
        default=all_engines
    )
    parser.add_argument("--output", "-o", help="Subdirectory to save results to. Default is `results`, e.g. bench_results/results",
        default=f"results"
    )
    args = parser.parse_args()

    if not set(args.benchmarks).issubset(set(all_benchmarks)):
        raise ValueError(f"Error: invalid benchmark name(s). Valid options are: {', '.join(all_benchmarks)}")

    if not set(args.engines).issubset(set(all_engines)):
        raise ValueError(f"Error: invalid engine name(s). Valid options are: {', '.join(all_engines)}")
    
    path = args.output

    # build and run everything
    call_buildscript()
    # make nice output directories
    os.makedirs(f"bench_results/{path}", exist_ok=True)
    os.makedirs(f"bench_results/{path}/charts/absolute_benchmarks", exist_ok=True)
    os.makedirs(f"bench_results/{path}/charts/absolute_engines", exist_ok=True)
    os.makedirs(f"bench_results/{path}/charts/relative", exist_ok=True)
    # get all the data we want
    get_binary_sizes(args.benchmarks,"binary_sizes", path)
    run_benchmarks(args.benchmarks, args.engines, "results", path)
    # make binary size chart
    os.system(f"python3 plot_binary_sizes.py bench_results/{path}/binary_sizes.json --benchmarks {' '.join(args.benchmarks)} -o bench_results/{path}/charts")
    # make runtime chart
    os.system(f"python3 plot_benchmarks.py bench_results/{path}/results_wasmfx.json bench_results/{path}/results_asyncify.json --benchmarks {' '.join(args.benchmarks)} --engines {' '.join(args.engines)} -o bench_results/{path}/charts")
    # clean up .wasm files and scripts
    subprocess.check_call(["make", "clean"])

if __name__ == "__main__":
    main()