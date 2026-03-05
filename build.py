#!/usr/bin/env python3
import argparse
import yaml
import sys
import os
from pathlib import Path

# Import config
config = yaml.safe_load(open("config.yml"))
BENCHMARKS = config["BENCHMARKS"]

# Given a benchmark name, build .wasm files for both asyncify and wasmfx modes.
def build_benchmarks(benchmark: str):
    os.system(f"make {benchmark}")
    
def wasmtime_precompile(benchmark: str):
    for mode in ["asyncify", "wasmfx"]:
        os.system(f"{config['WASMTIME_PATH']} compile -W=exceptions,function-references,gc,stack-switching -O opt-level=2 {benchmark}_{mode}.wasm -o {benchmark}_{mode}.cwasm")

def clean_all():
    os.system(f"make clean")
    
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
        "asyncify": "{prefix} setarch -R {wizard} --ext:stack-switching {benchmark}_asyncify.wasm {arg}",
        "wasmfx": "{prefix} setarch -R {wizard} --ext:stack-switching {benchmark}_wasmfx.wasm {arg}",
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
    elif benchmark in {"sieve", "sieve_switch"}:
        arg = config["SIEVE_ARGS"]
    else:
        arg = ""

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
                arg=arg
            )
            make_script(Path(script_name), content)

def benchmark_validation(benchmarks):
    for benchmark in benchmarks:
        if benchmark not in BENCHMARKS:
            print(f"Error: Benchmark '{benchmark}' is not recognized.")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-mode", "--mode", nargs="?", choices=["make-all", "clean-all"]
    )
    parser.add_argument(
        "-compile", "--compile", nargs="*", help="List of benchmarks", 
        default=None
    )
    parser.add_argument(
        "-gen-scripts", "--gen-scripts", nargs="*", help="List of benchmarks", 
        default=None
    )
    parser.add_argument(
        "-engines", "--engines", nargs="*", choices=list(ENGINES.keys()), help="List of engines", 
        default=ENGINES.keys()
    )

    args = parser.parse_args()

    if not (args.mode or args.compile or args.gen_scripts):
        print("Error: Must specify at least one of --mode, --compile, --gen-scripts")
        sys.exit(1)

    match args.mode:
        case "make-all":
            for benchmark in BENCHMARKS:
                build_benchmarks(benchmark)
                wasmtime_precompile(benchmark)
                generate_scripts(benchmark,args.engines)
                print("Built .wasm files and generated scripts for benchmark:", benchmark)
        case "clean-all":
            clean_all()
        case None:
            if args.compile:
                benchmark_validation(args.compile)
                for benchmark in args.compile:
                    build_benchmarks(benchmark)
                    wasmtime_precompile(benchmark)
                    print("Built .wasm files for benchmark:", benchmark)
            if args.gen_scripts:
                benchmark_validation(args.gen_scripts)
                for benchmark in args.gen_scripts:
                    generate_scripts(benchmark,args.engines)
                    print("Generated scripts for benchmark:", benchmark)
   
if __name__ == "__main__":
    main()
