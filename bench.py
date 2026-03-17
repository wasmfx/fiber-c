#!/usr/bin/env python3
"""
Script that calls buildscript and runs fiber-c benchmarks.
Usage:  `./bench.py --help`
        `./bench.py` # runs all benchmarks on all engines by default
        `./bench.py --benchmarks sieve1 itersum --engines d8 wasmtime`
"""
import argparse
import yaml
import sys
import os
import subprocess
import shutil
from pathlib import Path

config = yaml.safe_load(open("config.yml"))

all_benchmarks = config["BENCHMARKS_FIBER_C"]
all_engines = config["ENGINES"]

def call_buildscript(benchmark: str):
    subprocess.check_call(["./build.py", "--make", benchmark])
    
def run_benchmarks(benchmarks, engines):
    # call hyperfine to run wasmfx benchmarks
    subprocess.check_call (["hyperfine", "--warmup", "3", "--runs", "10", "--export-json", "bench_results/wasmfx_results.json", "--export-csv", "bench_results/wasmfx_results.csv", "-L", "benchmark", ",".join(benchmarks), "-L", "engine", ",".join(engines), "run-scripts/./{benchmark}_{engine}_wasmfx.sh"])
    # and now asyncify benchmarks
    subprocess.check_call(["hyperfine", "--warmup", "3", "--runs", "10", "--export-json", "bench_results/asyncify_results.json", "--export-csv", "bench_results/asyncify_results.csv", "-L", "benchmark", ",".join(benchmarks), "-L", "engine", ",".join(engines), "run-scripts/./{benchmark}_{engine}_asyncify.sh"])

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
    args = parser.parse_args()

    if not set(args.benchmarks).issubset(set(all_benchmarks)):
        raise ValueError(f"Error: invalid benchmark name(s). Valid options are: {', '.join(all_benchmarks)}")

    if not set(args.engines).issubset(set(all_engines)):
        raise ValueError(f"Error: invalid engine name(s). Valid options are: {', '.join(all_engines)}")

    for benchmark in args.benchmarks:
        call_buildscript(benchmark)

    os.makedirs("bench_results", exist_ok=True)
    run_benchmarks(args.benchmarks, args.engines)
     # make chart
    os.system(f"python3 plot_benchmarks.py bench_results/wasmfx_results.json bench_results/asyncify_results.json --benchmarks {' '.join(args.benchmarks)} --engines {' '.join(args.engines)} -o bench_results/results")
    # make a copy of the chart in the root directory of ehop machine for webserver reasons
    shutil.copytree("bench_results", "/opt/wasmfx/bench_results_page", dirs_exist_ok=True)
    # clean up .wasm files and scripts
    subprocess.check_call(["./build.py", "--clean-all"])

if __name__ == "__main__":
    main()
    
