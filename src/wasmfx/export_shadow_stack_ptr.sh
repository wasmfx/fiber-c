#!/bin/bash

# This script acts on .wat files produced by wasm-ld and exports the global
# variable corresponding to the shadow stack pointer, with name
# "__exported_shadow_stack_pointer". Since clang/wasm-ld turn all C globals into
# non-mut globals in wasm, the stack pointer should be the only *mutable* global
# in the wat file.

# Arguments:
# $1 Path of input wat file
# $2 Path where to write patched $1

# This regexp matches (global $foo (mut i32), but only actually captures the
# $foo part, so we can easily extract just the name of the global.
STACK_PTR_GLOBAL_REGEXP='(?<=\(global )(\$[^ ]*)(?= \(mut i32\))'

mut_global=$(grep --only-matching -P "$STACK_PTR_GLOBAL_REGEXP" "$1")
mut_globals_count=$(echo "$mut_global" | wc -l)


if (( mut_globals_count != 1 )); then
    echo "Did not find exactly one mutable i32 global, cannot identify stack pointer"
    exit 1
fi

echo "Stack pointer global variable: $mut_global"

sed 's/(global '"$mut_global"' (mut i32)/(global '"$mut_global"' (export "__exported_shadow_stack_pointer") (mut i32)/' "$1" > "$2"
