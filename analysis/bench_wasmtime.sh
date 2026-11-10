#!/bin/bash

# Benchmarks and their arguments
declare -A benchmarks
benchmarks["wasi_clock_treesum"]="25"
benchmarks["wasi_clock_pi"]=""
benchmarks["wasi_clock_itersum"]="100000000"
benchmarks["wasi_clock_c10m"]=""

modes=("asyncify" "wasmfx")
out="wasmtime_instrumented_results.csv"

# Set up output file
echo "benchmark,mode,ns" >> $out

# Run wasmtime benchmarks that don't need the stackpool allocator
for benchmark in "${!benchmarks[@]}"; do
    make $benchmark
    for mode in "${modes[@]}"; do
        echo "Running $benchmark-$mode"
        # In the case of c10m, run with appropriate wasmtime flags for stackpool allcator
        if [[ "$benchmark" == "wasi_clock_c10m" ]]; then
            setarch -R /opt/wasmfx/wasmfxtime/target/release/wasmtime run \
                --allow-precompiled -W=stack-switching \
                -O=pooling-allocator=y,pooling-max-tables-per-module=2,pooling-total-stacks=10001 \
                out/wasi_clock_c10m\_$mode.cwasm | 
            grep -oP '(?<=Execution time:)\d+' |
            while read -r ns; do
                echo "$benchmark,$mode,$ns" >> "$out"
            done
        # Otherwise, run without said flags
        else
            setarch -R /opt/wasmfx/wasmfxtime/target/release/wasmtime run \
                --allow-precompiled -W=stack-switching \
                out/$benchmark\_$mode.cwasm ${benchmarks[$benchmark]} | 
            grep -oP '(?<=Execution time:)\d+' |
            while read -r ns; do
                echo "$benchmark,$mode,$ns" >> "$out"
            done
        fi
    done
    make clean
done

make clean

python3 analysis/plot_v8_results.py $out