#!/usr/bin/env python3
import argparse
import yaml
import sys
import os
from pathlib import Path
import textwrap

config = yaml.safe_load(open("config.yml"))

all_benchmarks = config["BENCHMARKS"]
all_engines = config["ENGINES"]

def call_buildscript(benchmark: str):
    os.system(f"./build.py --compile {benchmark}")
    os.system(f"./build.py --gen-scripts {benchmark}")
    
def run_benchmarks(benchmarks, engines):
    # call hyperfine to run wasmfx benchmarks
    os.system(f"hyperfine --warmup 3 --runs 10 --export-json bench_results/wasmfx_results.json --export-csv bench_results/wasmfx_results.csv -L benchmark {','.join(benchmarks)} -L engine {','.join(engines)} './{{benchmark}}_{{engine}}_wasmfx.sh'")
    # and now asyncify benchmarks
    os.system(f"hyperfine --warmup 3 --runs 10 --export-json bench_results/asyncify_results.json --export-csv bench_results/asyncify_results.csv -L benchmark {','.join(benchmarks)} -L engine {','.join(engines)} './{{benchmark}}_{{engine}}_asyncify.sh'")

def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-benchmarks", "--benchmarks", nargs="*", help="List of benchmarks to run (sieve, itersum, treesum)", 
        default=all_benchmarks
    )
    parser.add_argument(
        "-engines", "--engines", nargs="*", help="List of engines to run (d8, wasmtime, wizard)", 
        default=all_engines
    )
    args = parser.parse_args()

    if not set(args.benchmarks).issubset(set(all_benchmarks)):
        print(f"Error: invalid benchmark name(s). Valid options are: {', '.join(all_benchmarks)}")
        exit(1)

    if not set(args.engines).issubset(set(all_engines)):
        print(f"Error: invalid engine name(s). Valid options are: {', '.join(all_engines)}")
        exit(1)

    for benchmark in args.benchmarks:
        call_buildscript(benchmark)

    os.system("mkdir -p bench_results")
    run_benchmarks(args.benchmarks, args.engines)
     # make chart
    os.system(f"python3 plot_benchmarks.py bench_results/wasmfx_results.json bench_results/asyncify_results.json --benchmarks {' '.join(args.benchmarks)} --engines {' '.join(args.engines)} -o results")
    # clean up .wasm files and scripts
    os.system("./build.py --mode clean-all")


if __name__ == "__main__":
    main()
    
