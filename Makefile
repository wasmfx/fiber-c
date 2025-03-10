ASYNCIFY_DEFAULT_STACK_SIZE?=2097152
STACK_POOL_SIZE?=0
WASMFX_CONT_TABLE_INITIAL_CAPACITY?=1024
WASMFX_PRESERVE_SHADOW_STACK?=1
# Only relevant if WASMFX_PRESERVE_SHADOW_STACK is 1
WASMFX_CONT_SHADOW_STACK_SIZE?=65536
ASYNCIFY=../binaryen/bin/wasm-opt --enable-exception-handling --enable-reference-types --enable-multivalue --enable-bulk-memory --enable-gc --enable-stack-switching -O2 -g --asyncify --no-inline="fiber_yield,fiber_yield_to,fiber_resume,fiber_resume_with"
WASICC=../benchfx/wasi-sdk-22.0/bin/clang
WASIFLAGS=-g --sysroot=../benchfx/wasi-sdk-22.0/share/wasi-sysroot -std=c17 -Wall -Wextra -Werror -Wpedantic -Wno-strict-prototypes -O0 -I inc
WASM_INTERP=../spec/interpreter/wasm
WASM_MERGE=../binaryen/bin/wasm-merge --enable-multimemory --enable-exception-handling --enable-reference-types --enable-multivalue --enable-bulk-memory --enable-gc --enable-stack-switching

ifeq ($(WASMFX_PRESERVE_SHADOW_STACK),1)
  SHADOW_STACK_FLAG=-DFIBER_WASMFX_PRESERVE_SHADOW_STACK
else
  SHADOW_STACK_FLAG=
endif

.PHONY: all
all: hello sieve itersum treesum

.PHONY: hello
hello: hello_asyncify.wasm hello_wasmfx.wasm hello_prompt_asyncify.wasm hello_forward_prompt_asyncify.wasm

hello_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/hello.c
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/hello.c -o hello_asyncfiy.pre.wasm
	$(ASYNCIFY) hello_asyncfiy.pre.wasm -o hello_asyncify.wasm
	chmod +x hello_asyncify.wasm

hello_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/hello.c
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/hello.c -o hello_wasmfx.pre.wasm
	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" hello_wasmfx.pre.wasm "main" -o hello_wasmfx.wasm
	chmod +x hello_wasmfx.wasm

hello_prompt_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_prompt_impl.c examples/prompt/hello.c
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_prompt_impl.c $(WASIFLAGS) examples/prompt/hello.c -o hello_prompt_asyncfiy.pre.wasm
	$(ASYNCIFY) hello_prompt_asyncfiy.pre.wasm -o hello_prompt_asyncify.wasm
	chmod +x hello_prompt_asyncify.wasm

hello_forward_prompt_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_prompt_impl.c examples/prompt/hello_forward.c
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_prompt_impl.c $(WASIFLAGS) examples/prompt/hello_forward.c -o hello_forward_prompt_asyncfiy.pre.wasm
	$(ASYNCIFY) hello_forward_prompt_asyncfiy.pre.wasm -o hello_forward_prompt_asyncify.wasm
	chmod +x hello_forward_prompt_asyncify.wasm


.PHONY: sieve
sieve: sieve_asyncify.wasm sieve_wasmfx.wasm

sieve_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/sieve.c
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/sieve.c -o sieve_asyncfiy.pre.wasm
	$(ASYNCIFY) sieve_asyncfiy.pre.wasm -o sieve_asyncify.wasm
	chmod +x sieve_asyncify.wasm

sieve_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/sieve.c
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/sieve.c -o sieve_wasmfx.pre.wasm
	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" sieve_wasmfx.pre.wasm "main" -o sieve_wasmfx.wasm
	chmod +x sieve_wasmfx.wasm

.PHONY: itersum
itersum: itersum_asyncify.wasm itersum_wasmfx.wasm

itersum_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/itersum.c
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/itersum.c -o itersum_asyncfiy.pre.wasm
	$(ASYNCIFY) itersum_asyncfiy.pre.wasm -o itersum_asyncify.wasm
	chmod +x itersum_asyncify.wasm

itersum_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/itersum.c
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/itersum.c -o itersum_wasmfx.pre.wasm
	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" itersum_wasmfx.pre.wasm "main" -o itersum_wasmfx.wasm
	chmod +x itersum_wasmfx.wasm

.PHONY: treesum
treesum: treesum_asyncify.wasm treesum_wasmfx.wasm

treesum_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/treesum.c
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/treesum.c -o treesum_asyncfiy.pre.wasm
	$(ASYNCIFY) treesum_asyncfiy.pre.wasm -o treesum_asyncify.wasm
	chmod +x treesum_asyncify.wasm

treesum_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/treesum.c
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/treesum.c -o treesum_wasmfx.pre.wasm
	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" treesum_wasmfx.pre.wasm "main" -o treesum_wasmfx.wasm
	chmod +x treesum_wasmfx.wasm


src/wasmfx/imports.wat: src/wasmfx/imports.wat.pp
	$(WASICC) -xc $(SHADOW_STACK_FLAG) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -E src/wasmfx/imports.wat.pp | sed 's/^#.*//g' > src/wasmfx/imports.wat

.PHONY: clean
clean:
	rm -f *.wasm
	rm -f src/wasmfx/imports.wat
