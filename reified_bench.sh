#!/bin/bash
set -e

# !!!!! Update the following to the right paths for your environment !!!!!
d8_path="/opt/wasmfx/v8-refied-fibers/out/x64.release/d8" 

# Array of benchmark-argument pairs
declare -A benchmarks
benchmarks["itersum"]=" 100000000"
benchmarks["roundrobin"]=""
benchmarks["pi"]=""

# Array of modes and corresponding V8 flags
declare -A modes
modes["wasmfx"]="--wasm-wasmfx"
modes["reified"]="--experimental-wasm-reified-fibers"

# compile binaries
make "${!benchmarks[@]}"

# Generate driver scripts for each benchmark-mode combination
driver_dir="run-scripts-reified"
mkdir -p "$driver_dir"

# Generate driver scripts for wasmtime-wasmfx runs (if we're doing them)
./build.py

for benchmark in "${!benchmarks[@]}"; do
    for mode in "${!modes[@]}"; do
        arg="${benchmarks[$benchmark]}"
        engine_options="${modes[$mode]}"
        engine_path="$d8_path"
        
        filename="${driver_dir}/${benchmark}_${mode}.sh"
        # Generate the script
        cat > "$filename" <<EOF
#!/bin/bash
setarch -R ${engine_path} ${engine_options} load.mjs -- out/${benchmark}_${mode}.wasm${arg}
EOF
        chmod +x "$filename"
        echo "Created driver script: $filename"
    done
    cp run-scripts/${benchmark}_wasmtime_wasmfx.sh ${driver_dir}
done

# Make string of comma-separated benchmarks/modes for hyperfine
benchmark_list=$(IFS=,; echo "${!benchmarks[*]}")
mode_list=$(IFS=,; echo "${!modes[*]}")

# Make results directory
mkdir -p reified_results

# Run benchmarks with hyperfine
hyperfine --warmup 3 --runs 10 -L benchmark $benchmark_list -L style $mode_list run-scripts-reified/{benchmark}_{style}.sh --export-json "reified_results/reified_results.json"


# Alternative experiment with wasmtime-wasmfx included for comparison

# !!!!! Update the following to the right paths for your environment !!!!!
# wasmtime_path="/opt/wasmfx/wasmtime/target/release/wasmtime"

# Run experiment
# hyperfine --warmup 3 --runs 10 -L benchmark $benchmark_list -L style $mode_list,wasmtime_wasmfx run-scripts-reified/{benchmark}_{style}.sh --export-json "reified_results/reified_results.json"

# Generate charts
python3 plot_benchmarks_reified.py reified_results/reified_results.json

# Clean up
make clean
