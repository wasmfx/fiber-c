# Fibers in C, compiled to Wasm!

This library provides a fiber abstraction meant as a basic building
block to build non-local control flow abstractions such as
async/await, yield-style generators, lightweight threads, first-class
continuations, and more, in C programs, and compiling said programs to
Wasm.

This library offers two backends:

1. Stackless fibers using the Asyncify transform of binaryen.
2. Native stackful fibers powered by the WasmFX instruction set.

## Installation
Clone the repository:
```
git clone https://github.com/wasmfx/fiber-c.git
```

## Building
To compile the benchmarks programs in `examples` from C to Wasm binaries, you will need:

1. [WASI-SDK 30.0](https://github.com/webassembly/wasi-sdk)
2. [Wasm reference interpreter from the stack-switching proposal](https://github.com/WebAssembly/stack-switching/tree/main/interpreter)
3. [Up-to-date Binaryen](https://github.com/WebAssembly/binaryen)
4. A Wasm execution engine with support for the stack switching instruction set, e.g. [Wasmtime](https://github.com/bytecodealliance/wasmtime), [V8 canary](https://chromium.googlesource.com/v8/v8/+/canary), or [Wizard](https://github.com/titzer/wizard-engine).


Please install and build these packages according to their docs. Please also make sure they are installed in the same root directory, 
then update the `ROOT` field of `make.config`.

**Note:** Instead of installing these dependencies manually, you can use the docker container build at http://github.com/wasmfx/benchtainer and run compilation/benchmarking runs within that container. See instructions therein.

After this, you should be able to run
```
make all
```
All binaries and compilation artefacts are stored in the `out` directory.

To discard all existing artefacts, run
```
make clean
```

## Running the benchmarks
The benchmarking script in `bench.py` can build, run, and time each benchmark. To get it working, you will need to:

1. Install and update engine dependencies 
    
    1. Wasmtime
    2. [V8](https://v8.dev/docs/build)
    3. [Wizard](https://github.com/titzer/wizard-engine/tree/master)

    You need to update the path to each engine in `config.yml`. 

2. Install [hyperfine](github.com/sharkdp/hyperfine)

3. Install python3 and the following dependencies for chart generation: pyyaml, matplotlib, numpy

You can now invoke the benchmarking script by running:
```
# run all benchmarks on all engines by default
./bench.py
```
which generates benchmarking scripts into the `/run-scripts` directory, and saves the benchmarking results
into `bench_results/results`. Charts displaying the absolute and relative runtimes of the benchmarks across
the WasmFX and Asyncify backends are saved to `bench_results/results/charts`.

You can also configure the benchmarks and engines you want to use:
```
# run selected benchmarks and engines, saves results to `bench_results/results_dir
./bench.py --benchmarks sieve1 itersum --engines d8 wasmtime -o results_dir
```

## Inspecting build artefacts
`bench.py` works by invoking `build.py`, which is responsible for invoking the Makefile
as well as generating scripts containing the commands for hyperfine to time (e.g. the scripts in the
`/run-scripts` directory). You can invoke `build.py` on its own to inspect these scripts without
starting the benchmarking process:

```
./build.py
```
