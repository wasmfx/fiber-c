# A generic set of make rules.
CONFIG=make.config
include ${CONFIG}

ifeq ($(WASMFX_PRESERVE_SHADOW_STACK),1)
  SHADOW_STACK_FLAG=-DFIBER_WASMFX_PRESERVE_SHADOW_STACK
else
  SHADOW_STACK_FLAG=
endif

.PHONY: all
all: out/$(BENCHMARK)_asyncify.wasm out/$(BENCHMARK)_wasmfx.wasm out/$(BENCHMARK)_asyncify.cwasm out/$(BENCHMARK)_wasmfx.cwasm

out/$(BENCHMARK)_asyncify.wasm: inc/fiber.h src/asyncify/asyncify_impl.c examples/$(BENCHMARK).c
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) examples/$(BENCHMARK).c -o $(BENCHMARK)_asyncify.pre.wasm
	$(ASYNCIFY) $(BENCHMARK)_asyncify.pre.wasm -o $(BENCHMARK)_asyncify.wasm
	chmod +x $(BENCHMARK)_asyncify.wasm

out/$(BENCHMARK)_wasmfx.wasm: inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c examples/$(BENCHMARK).c
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) examples/$(BENCHMARK).c -o $(BENCHMARK)_wasmfx.pre.wasm
	$(WASM_INTERP) -d -i src/wasmfx/imports.wat -o fiber_wasmfx_imports.wasm
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" $(BENCHMARK)_wasmfx.pre.wasm "main" -o $(BENCHMARK)_wasmfx.wasm
	chmod +x $(BENCHMARK)_wasmfx.wasm

out/$(BENCHMARK)_asyncify.cwasm: out/$(BENCHMARK)_asyncify.wasm
	$(WASMTIME) compile -W=exceptions,function-references,gc,stack-switching -O opt-level=2 $(BENCHMARK)_asyncify.wasm -o $(BENCHMARK)_asyncify.cwasm


out/$(BENCHMARK)_wasmfx.cwasm: out/$(BENCHMARK)_wasmfx.wasm
	$(WASMTIME) compile -W=exceptions,function-references,gc,stack-switching -O opt-level=2 $(BENCHMARK)_wasmfx.wasm -o $(BENCHMARK)_wasmfx.cwasm

src/wasmfx/imports.wat: src/wasmfx/imports.wat.pp
	$(WASICC) -xc $(SHADOW_STACK_FLAG) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -E src/wasmfx/imports.wat.pp | sed 's/^#.*//g' > src/wasmfx/imports.wat

src/wasmfx/imports_switch.wat: src/wasmfx/imports_switch.wat.pp
	$(WASICC) -xc $(SHADOW_STACK_FLAG) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -E src/wasmfx/imports_switch.wat.pp | sed 's/^#.*//g' > src/wasmfx/imports_switch.wat

.PHONY: clean
clean:
	rm -f *.wasm
	rm -f src/wasmfx/imports.wat src/wasmfx/imports_switch.wat
	rm -f *.sh
	rm -f *.cwasm
