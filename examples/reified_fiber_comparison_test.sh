#!/bin/bash

/binaryen/bin/wasm-as --enable-gc --enable-reified-fibers --enable-reference-types /reified_fiber_generator.wat

/stack-switching/interpreter/wasm -d -i /suspend_resume_generator.wat -o  /suspend_resume_generator.wasm

figlet fiber-c itersum wasmfx

time /v8/v8/out/x64.release/d8 --wasm-wasmfx /fiber-c/load.mjs -- /fiber-c/out/itersum_wasmfx.wasm 100000000
# V8 is running with experimental features enabled. Stability and security will suffer.
# 887459712
#
#
# real    0m5.113s
# user    0m5.106s
# sys     0m0.014s

figlet suspend_resume wat

time /v8/v8/out/x64.release/d8 --wasm-wasmfx /fiber-c/load.mjs -- /suspend_resume_generator.wasm
# V8 is running with experimental features enabled. Stability and security will suffer.
#
# real    0m3.170s
# user    0m3.166s
# sys     0m0.011s

figlet reified_fiber wat

time /v8/v8/out/x64.release/d8 --wasm-reified-fibers /fiber-c/load.mjs -- /reified_fiber_generator.wasm
# V8 is running with experimental features enabled. Stability and security will suffer.
#
# real    0m2.895s
# user    0m2.885s
# sys     0m0.012s

