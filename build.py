#!/usr/bin/env python3
"""
Buildscript that generates scripts to run them on the three wasm engines of interest (d8, wasmtime, and wizard). 
The generated scripts are in /run-scripts and can be executed with `./run-scripts/benchmark_engine_mode.sh`,
e.g. `./run-scripts/sieve1_d8_wasmfx.sh`.
Usage:  `./build.py --help`
        `./build.py --engines d8 wasmtime` to only generate scripts for d8 and wasmtime.
"""

import argparse
import yaml
import sys
import subprocess
from pathlib import Path

# Import config
config = yaml.safe_load(open("config.yml"))

# Given a benchmark name, build .wasm files for both asyncify and wasmfx modes.
def build_benchmarks():
    subprocess.run(["make", "all"])

# ---- Script generation ----

SCRIPT_TEMPLATE = f"#!/bin/bash\n setarch -R {{engine_path}} {{engine_options}} out/{{benchmark}}_{{mode}}.{{suffix}} {{arg}}"

def make_script(filename: Path, content: str):
    filename.write_text(content)
    filename.chmod(0o755)

def generate_scripts(benchmark: str, engines: list[str]):
    # Set arguments for benchmarks that need them
    if benchmark in {"itersum", "itersum_switch"}:
        arg = config["ITERSUM_ARGS"]
    elif benchmark in {"treesum", "treesum_switch"}:
        arg = config["TREESUM_ARGS"]
    elif benchmark in {"sieve", "sieve_switch"}:
        arg = config["SIEVE_ARGS"]
    else:
        arg = ""

    Path("run-scripts").mkdir(exist_ok=True)

    # Generate scripts that run each benchmark using SCRIPT_TEMPLATE and data from config.yml
    for engine in engines:
        for mode in ["asyncify", "wasmfx"]:
            script_name = f"{benchmark}_{engine}_{mode}.sh"
            # configure engine-specific options and script suffixes
            match engine:
                case "wasmtime":
                    engine_path=config["WASMTIME_PATH"]
                    suffix="cwasm"
                    # Set up stack pool size for the benchmarks that need a specific number
                    if benchmark in config["WASMTIME_STACK_POOL_SIZES"].keys():
                        engine_options = f"{config['WASMTIME_OPTIONS']},total-stacks={config['WASMTIME_STACK_POOL_SIZES'][benchmark]}"
                    else:
                        engine_options=config["WASMTIME_OPTIONS"]
                case "wizard":
                    engine_path=config["WIZARD_PATH"]
                    engine_options=config["WIZARD_OPTIONS"]
                    suffix="wasm"
                case "d8":
                    engine_path=config["D8_PATH"]
                    engine_options=config["D8_OPTIONS"]
                    suffix="wasm"
            # stick this all into the script template       
            content = SCRIPT_TEMPLATE.format(
                engine_path=engine_path,
                engine_options=engine_options,
                benchmark=benchmark,
                mode=mode,
                suffix=suffix,
                arg=arg, 
            )
            make_script(Path("run-scripts/" + script_name), content)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engines", nargs="*", choices=list(config["ENGINES"]), help="Build and generate scripts for specified engine(s)",
        default=config["ENGINES"]
    )
    args = parser.parse_args()
    build_benchmarks()
    for benchmark in config["BENCHMARKS_FIBER_C"]:
        generate_scripts(benchmark,args.engines)
        print("Generated scripts for benchmark:", benchmark)

if __name__ == "__main__":
    main()
