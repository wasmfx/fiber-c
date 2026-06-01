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
import os
import subprocess
import json

config = yaml.safe_load(open("config.yml"))

all_benchmarks = config["BENCHMARKS_FIBER_C"]
switch_benchmarks = config["BENCHMARKS_FIBER_C_SWITCH"]

all_engines = config["ENGINES"]


def disabled(engine, benchmark, style):
    if engine == "wasmtime" and style == "switch":
        return True
    return False


def generate_scripts():
    subprocess.check_call(["./build.py"])


def run_benchmarks(benchmarks, engines, filename, path):
    # call hyperfine to run wasmfx benchmarks
    subprocess.check_call(
        [
            "hyperfine",
            "--warmup",
            "1",
            "--runs",
            "10",
            "--export-json",
            f"bench_results/{path}/{filename}_wasmfx.json",
            "--export-csv",
            f"bench_results/{path}/{filename}_wasmfx.csv",
            "-L",
            "benchmark",
            ",".join(benchmarks),
            "-L",
            "engine",
            ",".join(engines),
            "run-scripts/{benchmark}_{engine}_wasmfx.sh",
        ]
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
            f"bench_results/{path}/{filename}_asyncify.json",
            "--export-csv",
            f"bench_results/{path}/{filename}_asyncify.csv",
            "-L",
            "benchmark",
            ",".join(benchmarks),
            "-L",
            "engine",
            ",".join(engines),
            "run-scripts/{benchmark}_{engine}_asyncify.sh",
        ]
    )


def get_binary_sizes(benchmarks, filename, path):
    data = []
    for benchmark in benchmarks:
        wasmfx_size = os.path.getsize(f"out/{benchmark}_wasmfx.stripped.wasm")
        asyncify_size = os.path.getsize(f"out/{benchmark}_asyncify.stripped.wasm")
        entry = {
            "benchmark": benchmark,
            "wasmfx": wasmfx_size,
            "asyncify": asyncify_size,
        }
        data.append(entry)
    with open(f"bench_results/{path}/{filename}.json", "w") as f:
        json.dump(data, f)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmarks",
        nargs="*",
        help="List of benchmarks to run (sieve, itersum, treesum)",
        default=all_benchmarks,
    )
    parser.add_argument(
        "--engines",
        nargs="*",
        help="List of engines to run (d8, wasmtime, wizard)",
        default=all_engines,
    )
    parser.add_argument(
        "--switch",
        help="Run switch experiments as well (benchmarks must have a switch counterpart, e.g. itersum and itersum_switch)",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Subdirectory to save results to. Default is `results`, e.g. bench_results/results",
        default="results",
    )
    args = parser.parse_args()

    # Some input validation
    if args.switch:
        if not set(args.benchmarks).issubset(set(switch_benchmarks)):
            raise ValueError(
                f"Error: invalid switch benchmark name(s). Valid options are: {', '.join(switch_benchmarks)}"
            )
        # Can't run switch experiments on wasmtime right now so we are banning that option
        if not set(args.engines).issubset(set(["d8", "wizard"])):
            raise ValueError(
                f"Error: invalid engine name(s). Valid options are: d8, wizard (switch experiments are currently broken on wasmtime)"
            )
    else:
        if not set(args.benchmarks).issubset(set(all_benchmarks)):
            raise ValueError(
                f"Error: invalid benchmark name(s). Valid options are: {', '.join(all_benchmarks)}"
            )
    if not set(args.engines).issubset(set(all_engines)):
        raise ValueError(
            f"Error: invalid engine name(s). Valid options are: {', '.join(all_engines)}"
        )

    path = args.output
    benchmarks_to_run = args.benchmarks

    # make nice output directories
    os.makedirs(f"bench_results/{path}", exist_ok=True)
    os.makedirs(f"bench_results/{path}/charts/absolute_benchmarks", exist_ok=True)
    os.makedirs(f"bench_results/{path}/charts/absolute_engines", exist_ok=True)
    os.makedirs(f"bench_results/{path}/charts/relative", exist_ok=True)
    # generate the benchmarking scripts
    generate_scripts()
    # compile the wasm binaries for each benchmark (the buildscript does this for both switch and non-switch benchmarks in the same call)
    for benchmark in benchmarks_to_run:
        subprocess.check_call(["make", benchmark])
    # if running switch experiments, update benchmarks to include switch versions of the selected benchmarks
    #    e.g. if user selects "itersum", also add "itersum_switch"
    if args.switch:
        benchmarks_to_run = list(
            zip([b + "_switch" for b in benchmarks_to_run], benchmarks_to_run)
        )
        benchmarks_to_run = list(sum(benchmarks_to_run, ()))  # flatten list of tuples
    # get binary size data
    get_binary_sizes(benchmarks_to_run, "binary_sizes", path)
    # make binary size chart
    subprocess.check_call(
        [
            "python3",
            "plot_binary_sizes.py",
            f"bench_results/{path}/binary_sizes.json",
            "--benchmarks",
            *benchmarks_to_run,
            "-o",
            f"bench_results/{path}/charts",
        ]
    )
    # run benchmarks to obtain runtime data
    run_benchmarks(benchmarks_to_run, args.engines, "results", path)
    # make runtime charts
    subprocess.check_call(
        [
            "python3",
            "plot_benchmarks.py",
            f"bench_results/{path}/results_wasmfx.json",
            f"bench_results/{path}/results_asyncify.json",
            "--benchmarks",
            *benchmarks_to_run,
            "--engines",
            *args.engines,
            "-o",
            f"bench_results/{path}/charts",
        ]
    )
    # Make extra charts for switch benchmarks
    if args.switch:
        # Put the extra charts in this directory
        os.makedirs(f"bench_results/{path}/charts/switch", exist_ok=True)
        # Run the switch-specific chart script on the wasmfx result file only
        subprocess.check_call(
            [
                "python3",
                "plot_benchmarks_switch.py",
                f"bench_results/{path}/results_wasmfx.json",
                "--benchmarks",
                *benchmarks_to_run,
                "--engines",
                *args.engines,
                "-o",
                f"bench_results/{path}/charts/switch",
            ]
        )


if __name__ == "__main__":
    main()
