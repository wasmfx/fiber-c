# A generic set of make rules.
CONFIG=make.config
include ${CONFIG}

ifeq ($(WASMFX_PRESERVE_SHADOW_STACK),1)
  SHADOW_STACK_FLAG=-DFIBER_WASMFX_PRESERVE_SHADOW_STACK
else
  SHADOW_STACK_FLAG=
endif

.PHONY: all
BENCHMARKS=c10m hello itersum pi sieve simple skynet state treesum treesumlinear
# treesum_switch itersum_switch hello_switch

# This strange invocation tells make not to delete "intermediate products".
.SECONDARY:

all: $(BENCHMARKS)

%: out/%_asyncify.wasm out/%_wasmfx.wasm out/%_asyncify.cwasm out/%_wasmfx.cwasm
	@echo Made $@ #from $^

out/%_asyncify.wasm: examples/%.c inc/fiber.h src/asyncify/asyncify_impl.c | out
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) $< -o $(@:.wasm=.pre.wasm)
	$(ASYNCIFY) $(@:.wasm=.pre.wasm) -o $@
	chmod +x $@

fiber_switch_wasmfx_imports.wasm: src/wasmfx/imports_switch.wat
	$(WASM_INTERP) -d -i src/wasmfx/imports_switch.wat -o fiber_switch_wasmfx_imports.wasm

fiber_wasmfx_imports.wasm: src/wasmfx/imports.wat
	$(WASM_INTERP) -d -i $< -o $@

out/%_wasmfx.wasm: examples/%.c inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c fiber_wasmfx_imports.wasm | out
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) $< -o $(@:.wasm=.pre.wasm)
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" $(@:.wasm=.pre.wasm) "main" -o $@
	chmod +x $@

out/%_switch_wasmfx.wasm: examples/%.c inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c fiber_switch_wasmfx_imports.wasm | out
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) $< -o $(@:.wasm=.pre.wasm)
	$(WASM_MERGE) fiber_switch_wasmfx_imports.wasm "fiber_switch_wasmfx_imports" $(@:.wasm=.pre.wasm) "main" -o $@
	chmod +x $@

out/%_asyncify.cwasm: out/%_asyncify.wasm
	$(WASMTIME) compile -W=exceptions,function-references,gc,stack-switching -O opt-level=2 $< -o $@

out/%_wasmfx.cwasm: out/%_wasmfx.wasm
	$(WASMTIME) compile -W=exceptions,function-references,gc,stack-switching -O opt-level=2 $< -o $@

src/wasmfx/imports.wat: src/wasmfx/imports.wat.pp
	$(WASICC) -xc $(SHADOW_STACK_FLAG) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -E src/wasmfx/imports.wat.pp | sed 's/^#.*//g' > src/wasmfx/imports.wat

src/wasmfx/imports_switch.wat: src/wasmfx/imports_switch.wat.pp
	$(WASICC) -xc $(SHADOW_STACK_FLAG) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -E src/wasmfx/imports_switch.wat.pp | sed 's/^#.*//g' > src/wasmfx/imports_switch.wat

.PHONY: out
out:
	mkdir -p out

.PHONY: clean
clean:
	rm -f *.wasm
	rm -f src/wasmfx/imports.wat src/wasmfx/imports_switch.wat
	rm -f *.sh
	rm -f *.cwasm
	rm -rf run-scripts out
