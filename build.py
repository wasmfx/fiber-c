#!/usr/bin/env python3
"""
Buildscript that compiles wasm binaries for fiber-c benchmarks, and generates scripts to run them on the three wasm engines of interest
(d8, wasmtime, and wizard). The generated scripts are in /run-scripts and can be executed with `./run-scripts/benchmark_engine_mode.sh`,
e.g. `./run-scripts/sieve1_d8_wasmfx.sh`.
Usage:  `./build.py --help`
        `./build.py --make-all`
        `./build.py --make sieve1 --engines d8 wasmtime`
        `./build.py --clean-all`
"""

import argparse
import yaml
import sys
import subprocess
from pathlib import Path

# Import config
config = yaml.safe_load(open("config.yml"))
BENCHMARKS = config["BENCHMARKS_FIBER_C"]

# Given a benchmark name, build .wasm files for both asyncify and wasmfx modes.
# TODO: Move the output files to a more sensible directory, such as /benchfx/out/benchmark_name
def build_benchmarks(benchmark: str):
    subprocess.run(["make", f"BENCHMARK={benchmark}"])

def clean_all():
    subprocess.run(["make", "clean"])

# ---- Script generation ----
ENGINES = {
    "wasmtime": {
        "asyncify": "{prefix} setarch -R {wasmtime} run --allow-precompiled -W=exceptions,function-references,gc,stack-switching {benchmark}_asyncify.cwasm {arg}",
        "wasmfx": "{prefix} setarch -R {wasmtime} run --allow-precompiled -W=exceptions,function-references,gc,stack-switching {benchmark}_wasmfx.cwasm {arg}"
    },

    "d8": {
        "asyncify": "{prefix} setarch -R {d8} --experimental-wasm-wasmfx {v8_js_loader} -- {benchmark}_asyncify.wasm {arg}",
        "wasmfx": "{prefix} setarch -R {d8} --experimental-wasm-wasmfx {v8_js_loader} -- {benchmark}_wasmfx.wasm {arg}",
    },

    "wizard": {
        "asyncify": "{prefix} setarch -R {wizard} {wizard_flags} --mode=jit {benchmark}_asyncify.wasm {arg}",
        "wasmfx": "{prefix} setarch -R {wizard} {wizard_flags} --mode=jit {benchmark}_wasmfx.wasm {arg}",
    },
}

def make_script(filename: Path, content: str):
    filename.write_text(content)
    filename.chmod(0o755)

def generate_scripts(benchmark: str, engines: list[str]):
    # Set arguments for benchmarks that need them
    if benchmark in {"itersum", "itersum_switch"}:
        arg = config["ITERSUM_ARGS"]
    elif benchmark in {"treesum", "treesum_switch"}:
        arg = config["TREESUM_ARGS"]
    elif benchmark in {"sieve1", "sieve1_switch"}:
        arg = config["SIEVE1_ARGS"]
    else:
        arg = ""

    Path("run-scripts").mkdir(exist_ok=True)
    for engine in engines:
        for mode, template in ENGINES[engine].items():
            script_name = f"{benchmark}_{engine}_{mode}.sh"
            content = template.format(
                prefix=config["PREFIX"],
                benchmark=benchmark,
                wasmtime=config["WASMTIME_PATH"],
                d8=config["D8_PATH"],
                wizard=config["WIZARD_PATH"],
                v8_js_loader=config["V8_JS_LOADER"],
                arg=arg,
                wizard_flags=config["WIZARD_FLAGS"],
            )
            make_script(Path("run-scripts/" + script_name), content)

def benchmark_validation(benchmarks):
    for benchmark in benchmarks:
        if benchmark not in BENCHMARKS:
            raise ValueError(f"Error: Benchmark '{benchmark}' is not recognized.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--make-all", action="store_true", help="Build and generate scripts for all benchmarks"
    )
    parser.add_argument(
        "--clean-all", action="store_true", help="Clean all build artefacts"
    )
    parser.add_argument(
        "--make", nargs="*", help="Build and generate scripts for specified benchmark(s)",
        default=None
    )
    parser.add_argument(
        "--engines", nargs="*", choices=list(ENGINES.keys()), help="Build and generate scripts for specified engine(s)",
        default=ENGINES.keys()
    )

    args = parser.parse_args()

    if not (args.make_all or args.clean_all or args.make):
        print("Error: Must specify at least one of --make-all, --clean-all, --make")
        sys.exit(1)

    if args.make_all:
        for benchmark in BENCHMARKS:
            print("Building benchmark:", benchmark)
            build_benchmarks(benchmark)
            generate_scripts(benchmark,args.engines)
            print("Built .wasm files and generated scripts for benchmark:", benchmark)
    elif args.clean_all:
        clean_all()
    elif args.make:
        benchmark_validation(args.make)
        for benchmark in args.make:
            build_benchmarks(benchmark)
            generate_scripts(benchmark,args.engines)
            print("Built .wasm files and generated scripts for benchmark:", benchmark)
    else:
        raise ValueError("Error: Invalid arguments. Use --help for usage instructions.")

if __name__ == "__main__":
    main()
