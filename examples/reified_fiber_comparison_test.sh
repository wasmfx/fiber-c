#!/bin/bash

set -e

ROOT=${ROOT:-/opt/wasmfx}
FIBER_C=${FIBER_C:-$(pwd)/fiber-c}

$ROOT/binaryen/bin/wasm-as --enable-gc --enable-reified-fibers --enable-reference-types ${FIBER_C}/examples/reified_fibers_generator.wat

$ROOT/stack-switching/interpreter/wasm -d -i ${FIBER_C}/examples/suspend_resume_generator.wat -o  ${FIBER_C}/examples/suspend_resume_generator.wasm

figlet -f small v8 fiber-c itersum wasmfx

hyperfine "$ROOT/v8/v8/out/x64.release/d8 --wasm-wasmfx ${FIBER_C}/load.mjs -- ${FIBER_C}/out/itersum_wasmfx.wasm 100000000"
# V8 is running with experimental features enabled. Stability and security will suffer.
# 887459712
#
#
# real    0m5.113s
# user    0m5.106s
# sys     0m0.014s

figlet -f small v8 suspend_resume wat

hyperfine "$ROOT/v8/v8/out/x64.release/d8 --wasm-wasmfx ${FIBER_C}/load.mjs -- ${FIBER_C}/examples/suspend_resume_generator.wasm"
# V8 is running with experimental features enabled. Stability and security will suffer.
#
# real    0m3.170s
# user    0m3.166s
# sys     0m0.011s

figlet -f small v8 reified_fiber wat

hyperfine "$ROOT/v8/v8/out/x64.release/d8 --wasm-reified-fibers ${FIBER_C}/load.mjs -- ${FIBER_C}/examples/reified_fibers_generator.wasm"
# V8 is running with experimental features enabled. Stability and security will suffer.
#
# real    0m2.895s
# user    0m2.885s
# sys     0m0.012s


figlet -f small wasmtime fiber-c itersum wasmfx

hyperfine "$ROOT/wasmfxtime/target/release/wasmtime -W function-references,stack-switching,exceptions ${FIBER_C}/out/itersum_wasmfx.wasm 100000000"
# V8 is running with experimental features enabled. Stability and security will suffer.
# 887459712
#
#
# real    0m5.113s
# user    0m5.106s
# sys     0m0.014s

figlet -f small wasmtime suspend_resume wat

hyperfine "$ROOT/wasmfxtime/target/release/wasmtime -W function-references,stack-switching,exceptions ${FIBER_C}/examples/suspend_resume_generator.wasm"
# V8 is running with experimental features enabled. Stability and security will suffer.
#
# real    0m3.170s
# user    0m3.166s
# sys     0m0.011s
