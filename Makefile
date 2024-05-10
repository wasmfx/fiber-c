ASYNCIFY_DEFAULT_STACK_SIZE?=2097152
WASMFX_CONT_TABLE_INITIAL_CAPACITY?=1024
ASYNCIFY=../benchfx/binaryenfx/bin/wasm-opt --enable-exception-handling --enable-reference-types --enable-multivalue --enable-bulk-memory --enable-gc --enable-typed-continuations -O2 --asyncify
WASICC=../benchfx/wasi-sdk-22.0/bin/clang
WASIFLAGS=--sysroot=../benchfx/wasi-sdk-22.0/share/wasi-sysroot -std=c17 -Wall -Wextra -Werror -Wpedantic -Wno-strict-prototypes -O3 -I inc
WASM_INTERP=../spec/interpreter/wasm
WASM_MERGE=../benchfx/binaryenfx/bin/wasm-merge --enable-multimemory --enable-exception-handling --enable-reference-types --enable-multivalue --enable-bulk-memory --enable-gc --enable-typed-continuations

.PHONY: hello
hello: hello_asyncify.wasm hello_wasmfx.wasm

hello_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/hello.c
	$(WASICC) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/hello.c -o hello_asyncfiy.pre.wasm
	$(ASYNCIFY) hello_asyncfiy.pre.wasm -o hello_asyncify.wasm
	chmod +x hello_asyncify.wasm

hello_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/hello.c
	$(WASICC) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/hello.c -o hello_wasmfx.pre.wasm
	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" hello_wasmfx.pre.wasm "main" -o hello_wasmfx.wasm
	chmod +x hello_wasmfx.wasm

.PHONY: sieve
sieve: sieve_asyncify.wasm sieve_wasmfx.wasm

sieve_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/sieve.c
	$(WASICC) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/sieve.c -o sieve_asyncfiy.pre.wasm
	$(ASYNCIFY) sieve_asyncfiy.pre.wasm -o sieve_asyncify.wasm
	chmod +x sieve_asyncify.wasm

sieve_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/sieve.c
	$(WASICC) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/sieve.c -o sieve_wasmfx.pre.wasm
	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" sieve_wasmfx.pre.wasm "example" -o sieve_wasmfx.wasm
	chmod +x sieve_wasmfx.wasm

src/wasmfx/imports.wat: src/wasmfx/imports.wat.pp
	$(WASICC) -xc -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -E src/wasmfx/imports.wat.pp | tail -n+8 > src/wasmfx/imports.wat

.PHONY: clean
clean:
	rm -f *.wasm
	rm -f src/wasmfx/imports.wat
