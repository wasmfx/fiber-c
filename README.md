# Fibers in C, compiled to Wasm!

This library provides a fiber abstraction meant as a basic building
block to build non-local control flow abstractions such as
async/await, yield-style generators, lightweight threads, first-class
continuations, and more, in C programs, and compiling said programs to
Wasm.

This library offers two backends:

1. An Asyncify-based implementation, which provides a stackless
implementation of fibers.
2. A WasmFX powered implementation, which provides a native stackful
implementation of fibers.
