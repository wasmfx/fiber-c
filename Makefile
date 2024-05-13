ASYNCIFY_DEFAULT_STACK_SIZE?=2097152
WASMFX_CONT_TABLE_INITIAL_CAPACITY?=1024
WASMFX_PRESERVE_SHADOW_STACK?=1
# Only relevant if WASMFX_PRESERVE_SHADOW_STACK is 1
WASMFX_CONT_SHADOW_STACK_SIZE?=65536
ASYNCIFY=../benchfx/binaryenfx/bin/wasm-opt --enable-exception-handling --enable-reference-types --enable-multivalue --enable-bulk-memory --enable-gc --enable-typed-continuations -O2 --asyncify
WASICC=../benchfx/wasi-sdk-22.0/bin/clang
WASIFLAGS=--sysroot=../benchfx/wasi-sdk-22.0/share/wasi-sysroot -std=c17 -Wall -Wextra -Werror -Wpedantic -Wno-strict-prototypes -O3 -I inc
WASM_INTERP=../spec/interpreter/wasm
WASM_MERGE=../benchfx/binaryenfx/bin/wasm-merge --enable-multimemory --enable-exception-handling --enable-reference-types --enable-multivalue --enable-bulk-memory --enable-gc --enable-typed-continuations

ifeq ($(WASMFX_PRESERVE_SHADOW_STACK),1)
  SHADOW_STACK_FLAG=-DFIBER_WASMFX_PRESERVE_SHADOW_STACK
else
  SHADOW_STACK_FLAG=
endif


.PHONY: hello
hello: hello_asyncify.wasm hello_wasmfx.wasm

hello_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/hello.c
	$(WASICC) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/hello.c -o hello_asyncfiy.pre.wasm
	$(ASYNCIFY) hello_asyncfiy.pre.wasm -o hello_asyncify.wasm
	chmod +x hello_asyncify.wasm

hello_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/hello.c
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/hello.c -o hello_wasmfx.pre.wasm

	# Export stack pointer global as __exported_shadow_stack_pointer
	$(WASM_INTERP) -d -i hello_wasmfx.pre.wasm -o hello_wasmfx.pre.wat
	src/wasmfx/export_shadow_stack_ptr.sh hello_wasmfx.pre.wat hello_wasmfx.patched_pre.wat
	$(WASM_INTERP) -d -i  hello_wasmfx.patched_pre.wat -o hello_wasmfx.patched_pre.wasm

	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" hello_wasmfx.patched_pre.wasm "main" -o hello_wasmfx.wasm
	chmod +x hello_wasmfx.wasm

.PHONY: sieve
sieve: sieve_asyncify.wasm sieve_wasmfx.wasm

sieve_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/sieve.c
	$(WASICC) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/sieve.c -o sieve_asyncfiy.pre.wasm
	$(ASYNCIFY) sieve_asyncfiy.pre.wasm -o sieve_asyncify.wasm
	chmod +x sieve_asyncify.wasm

sieve_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/sieve.c
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/sieve.c -o sieve_wasmfx.pre.wasm

	# Export stack pointer global as __exported_shadow_stack_pointer
	$(WASM_INTERP) -d -i sieve_wasmfx.pre.wasm -o sieve_wasmfx.pre.wat
	src/wasmfx/export_shadow_stack_ptr.sh sieve_wasmfx.pre.wat sieve_wasmfx.patched_pre.wat
	$(WASM_INTERP) -d -i  sieve_wasmfx.patched_pre.wat -o sieve_wasmfx.patched_pre.wasm

	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" sieve_wasmfx.patched_pre.wasm "main" -o sieve_wasmfx.wasm
	chmod +x sieve_wasmfx.wasm

src/wasmfx/imports.wat: src/wasmfx/imports.wat.pp
	$(WASICC) -xc $(SHADOW_STACK_FLAG) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -E src/wasmfx/imports.wat.pp | sed 's/^#.*//g' > src/wasmfx/imports.wat

.PHONY: clean
clean:
	rm -f *.wasm
	rm -f src/wasmfx/imports.wat
