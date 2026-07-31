#!/usr/bin/env python3
"""
Script that runs the treesum benchmark with different arguments, to illustrate
the stack depth at which wasmfx outperforms asyncify.

The range of arguments is specified in config.yml under TREESUM_VARIED_ARGS.

Usage:  `./treesum_bench.py`
"""


import yaml
import subprocess
from pathlib import Path

# Import config
config = yaml.safe_load(open("config.yml"))

def run_benchmarks(args, engines, show_output=False):
    # call hyperfine to run wasmfx benchmarks
    subprocess.check_call(
        [
            "hyperfine",
            "--warmup",
            "1",
            "--runs",
            "10",
            "--export-json",
            f"bench_results/treesum/treesum_wasmfx.json",
            "--export-csv",
            f"bench_results/treesum/treesum_wasmfx.csv",
            "-L",
            "arg",
            ",".join(args),
            "-L",
            "engine",
            ",".join(engines),
            "-L",
            "style",
            "wasmfx",
            "run-scripts/treesum/treesum_{arg}_{engine}_wasmfx.sh",
        ] + (["--show-output"] if show_output else [])
    )
    # and now asyncify benchmarks
    subprocess.check_call(
        [
            "hyperfine",
            "--warmup",
            "1",
            "--runs",
            "10",
            "--export-json",
            f"bench_results/treesum/treesum_asyncify.json",
            "--export-csv",
            f"bench_results/treesum/treesum_asyncify.csv",
            "-L",
            "arg",
            ",".join(args),
            "-L",
            "engine",
            ",".join(engines),
            "-L",
            "style",
            "asyncify",
            "run-scripts/treesum/treesum_{arg}_{engine}_asyncify.sh",
        ] + (["--show-output"] if show_output else [])
    )

def main():
   # Make output directory
    Path("bench_results/treesum").mkdir(exist_ok=True)

    # Compile the treesum binary
    subprocess.check_call(["make", "treesum"])

    # Generate run-scripts for treesum with different arguments
    subprocess.check_call(["./build.py"])

    # Run benchmarks
    run_benchmarks([str(x) for x in config["TREESUM_VARIED_ARGS"]], ["wasmtime"], show_output=False)

    # Make chart from data
    subprocess.check_call(["python3", 
        "plot_treesum.py", 
        "bench_results/treesum", 
        "-o", "bench_results/treesum"])


if __name__ == "__main__":
    main()
