PATH_TO_DIR=experiments/lotsa-tags

# Number of tags
NUM_TAGS=100

# List of tags to suspend with, corresponding to their position in the list of tags
declare -a SUSPEND_TO_TAGS=("1" "25" "50" "75" "100")

# Generate the binaries
for i in ${SUSPEND_TO_TAGS[@]};
do
  bash experiments/lotsa-tags/gen_lotsa_tags.sh 100 $i
done

# Generate the driver scripts
mkdir -p ${PATH_TO_DIR}/run-scripts-tags

for i in ${SUSPEND_TO_TAGS[@]}; do
        filename="${PATH_TO_DIR}/run-scripts-tags/itersum_100_tags_${i}.sh"
        # Generate the script
        cat > "$filename" <<EOF
#!/bin/bash
setarch -R /opt/wasmfx/v8/out/x64.release/d8 --wasm-wasmfx --wasm-wasmfx load.mjs -- examples/tags/itersum_100_tags_${i}.wasm |& :
EOF
        chmod +x "$filename"
        echo "Created driver script: $filename"
done

# Make string of comma-separated tags for hyperfine
IFS=,
tags_list=$(echo "${SUSPEND_TO_TAGS[*]}")

# V8 experiment
hyperfine --warmup 1 --runs 10 -L number "$tags_list" ${PATH_TO_DIR}/run-scripts-tags/itersum_${NUM_TAGS}_tags_{number}.sh --export-csv "lotsa_tags_bench.csv"

# Wasmtime experiment
# hyperfine --warmup 1 --runs 10 -L number "$tags_list" ${PATH_TO_DIR}/run-scripts-tags/itersum_${NUM_TAGS}_tags_{number}.sh --export-csv "lotsa_tags_bench.csv"

# Perf measurements
# for i in ${SUSPEND_TO_TAGS[@]}; do
#     echo "Running benchmark $i"
#     sudo perf stat -e cycles,task-clock -x , /home/yinamy/wasmfx/fiber-c/run-scripts-tags/itersum_100_tags_${i}.sh &>> lotsa_tags_bench.txt
# done

# Clean up
# rm examples/itersum.wasm
# rm examples/itersum_${args[0]}_tags.wasm