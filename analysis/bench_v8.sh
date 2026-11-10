#!/bin/bash

benchmarks=("treesum" "pi" "itersum" "c10m")
modes=("asyncify" "wasmfx")
out="v8_results.csv"

# Generate driver scripts
./build.py

# Set up output file
echo "benchmark,mode,ns" >> $out

# Run V8 benchmarks
for benchmark in "${benchmarks[@]}"; do
    make $benchmark\_v8
    for mode in "${modes[@]}"; do
        echo "Running $benchmark-$mode"
        setarch -R /opt/wasmfx/v8/v8/out/x64.release/d8 --experimental-wasm-wasmfx load_instrumented.mjs -- out/$benchmark\_v8\_$mode.wasm | 
        grep -oP '(?<=Execution time:)\d+' |
        while read -r ns; do
            echo "$benchmark,$mode,$ns" >> "$out"
        done
    done
    make clean
done

make clean

python3 plot_v8_results.py $out