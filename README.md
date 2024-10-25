# Fibers in C, compiled to Wasm!

This library provides a fiber abstraction meant as a basic building
block to build non-local control flow abstractions such as
async/await, yield-style generators, lightweight threads, first-class
continuations, and more, in C programs, and compiling said programs to
Wasm.

This library offers two backends:

1. Stackless fibers using the Asyncify transform of binaryen.
2. Native stackful fibers powered by the WasmFX instruction set.
