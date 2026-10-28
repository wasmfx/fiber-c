# Script that adds n tags to a version of itersum.wat
args=("$@")

# Make output directory for new .wats
mkdir -p examples/tags

# Generate the new tags
tags=$(for i in $(seq 1 ${args[0]}); do 
        printf "  (tag \$yield_${i} (param i32))\n"; 
    done)

# Generate handlers for each of the new tags
hdls=$(for i in $(seq 1 ${args[0]}); do 
        printf "          (on \$yield_${i} \$on_yield)\n";
    done)

# Replace the existing $yield tag with the n new tags
# Also replace the existing handler with the n new handlers
awk -v tags="$tags" -v hdls="$hdls" '
/^  \(tag \$yield \(param i32\)\)$/ {
    printf "%s\n", tags
    next
}

/^          \(on \$yield \$on_yield\)$/ {
    printf "%s\n", hdls
    next
}

{ print }
' "examples/itersum.wat" > examples/tags/itersum_${args[0]}_tags_${args[1]}.wat

# Replace calls to $yield with a call to the user-specified-numbered tag
sed -i "s/\$yield /\$yield_${args[1]} /g" "examples/tags/itersum_${args[0]}_tags_${args[1]}.wat"

# Compile normal itersum.wat
/opt/wasmfx/binaryen/bin/wasm-as --enable-gc --enable-stack-switching --enable-reference-types --enable-exception-handling --enable-multivalue examples/itersum.wat

# Compile the new file
/opt/wasmfx/binaryen/bin/wasm-as --enable-gc --enable-stack-switching --enable-reference-types --enable-exception-handling --enable-multivalue examples/tags/itersum_${args[0]}_tags_${args[1]}.wat

# Run wasm-opt on them
# /opt/wasmfx/binaryen/bin/wasm-opt --enable-gc --enable-stack-switching --enable-reference-types --enable-exception-handling --enable-multivalue -O3 -Oz examples/tags/itersum_${args[0]}_tags_${args[1]}.wasm -o examples/tags/itersum_${args[0]}_tags_${args[1]}.wasm