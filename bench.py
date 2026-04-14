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

def call_buildscript():
    subprocess.check_call(["./build.py"])
    
def run_benchmarks(benchmarks, engines, filename):
    # call hyperfine to run wasmfx benchmarks
    subprocess.check_call (["hyperfine", "--warmup", "3", "--runs", "10", "--export-json", f"bench_results/{filename}_wasmfx.json", "--export-csv", f"bench_results/{filename}_wasmfx.csv", "-L", "benchmark", ",".join(benchmarks), "-L", "engine", ",".join(engines), "run-scripts/./{benchmark}_{engine}_wasmfx.sh"])
    # and now asyncify benchmarks
    subprocess.check_call(["hyperfine", "--warmup", "3", "--runs", "10", "--export-json", f"bench_results/{filename}_asyncify.json", "--export-csv", f"bench_results/{filename}_asyncify.csv", "-L", "benchmark", ",".join(benchmarks), "-L", "engine", ",".join(engines), "run-scripts/./{benchmark}_{engine}_asyncify.sh"])

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
    parser.add_argument("--output", "-o", help="Filename to save results to. Default is `results`, such that is output live in bench_results/results_{backend}",
        default=f"results"
    )
    args = parser.parse_args()

    if not set(args.benchmarks).issubset(set(all_benchmarks)):
        raise ValueError(f"Error: invalid benchmark name(s). Valid options are: {', '.join(all_benchmarks)}")

    if not set(args.engines).issubset(set(all_engines)):
        raise ValueError(f"Error: invalid engine name(s). Valid options are: {', '.join(all_engines)}")

    # build and run everything
    call_buildscript()
    os.makedirs("bench_results", exist_ok=True)
    run_benchmarks(args.benchmarks, args.engines, args.output)
     # make chart
    os.system(f"python3 plot_benchmarks.py bench_results/{args.output}_wasmfx.json bench_results/{args.output}_asyncify.json --benchmarks {' '.join(args.benchmarks)} --engines {' '.join(args.engines)} -o bench_results/{args.output}")
    # clean up .wasm files and scripts
    subprocess.check_call(["make", "clean"])

if __name__ == "__main__":
    main()