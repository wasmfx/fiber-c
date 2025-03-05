make clean 
make all

bench_named_wasmfx_asyncify() {
    hyperfine -w 20 -L program $1_named_asyncify,$1_named_wasmfx "../wasmfxtime/target/debug/wasmtime -W=exceptions,function-references,stack-switching {program}.wasm $2"
}

bench_named_unnamed() {
    hyperfine -w 20 -N -L program $1_wasmfx,$1_named_wasmfx "../wasmfxtime/target/debug/wasmtime -W=exceptions,function-references,stack-switching {program}.wasm $2"
}

bench_named_unnamed_precompiled_release() {
    hyperfine -w 20 -N -L program $1_wasmfx,$1_named_wasmfx "../wasmfxtime/target/release/wasmtime -W=exceptions,function-references,stack-switching --allow-precompiled {program}.cwasm $2"
}

# bench_named_wasmfx_asyncify "itersum" "1500"
# bench_named_wasmfx_asyncify "treesum" "25"
# bench_named_wasmfx_asyncify "sieve" "100"

bench_named_unnamed "itersum" "2000"
bench_named_unnamed "treesum" "25"
bench_named_unnamed "sieve" "10"


