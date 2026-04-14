# A generic set of make rules.
CONFIG=make.config
include ${CONFIG}

ifeq ($(WASMFX_PRESERVE_SHADOW_STACK),1)
  SHADOW_STACK_FLAG=-DFIBER_WASMFX_PRESERVE_SHADOW_STACK
else
  SHADOW_STACK_FLAG=
endif

.PHONY: all
BENCHMARKS= hello c10m hello itersum pi sieve skynet state treesum treesumlinear
SWITCH_BENCHMARKS= hello itersum treesum

# This strange invocation tells make not to delete "intermediate products".
.SECONDARY:

all: $(BENCHMARKS) $(SWITCH_BENCHMARKS)

%: out/%_asyncify.wasm out/%_wasmfx.wasm out/%_asyncify.cwasm out/%_wasmfx.cwasm
	@echo Made $@ #from $^

$(SWITCH_BENCHMARKS): %: out/%_switch_asyncify.wasm out/%_switch_wasmfx.wasm

out/%_asyncify.wasm: examples/%.c inc/fiber.h src/asyncify/asyncify_impl.c | out
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_impl.c $(WASIFLAGS) $< -o $(@:.wasm=.pre.wasm)
	$(ASYNCIFY) $(@:.wasm=.pre.wasm) -o $@
	chmod +x $@

out/%_switch_asyncify.wasm: examples/%_switch.c inc/fiber_switch.h src/asyncify/asyncify_impl.c | out
	$(WASICC) -DSTACK_POOL_SIZE=$(STACK_POOL_SIZE) -DASYNCIFY_DEFAULT_STACK_SIZE=$(ASYNCIFY_DEFAULT_STACK_SIZE) src/asyncify/asyncify_switch_impl.c $(WASIFLAGS) $< -o $(@:.wasm=.pre.wasm)
	$(ASYNCIFY) $(@:.wasm=.pre.wasm) -o $@
	chmod +x $@

fiber_wasmfx_imports.wasm: src/wasmfx/imports.wat
	$(WASM_INTERP) -d -i $< -o $@

fiber_switch_wasmfx_imports.wasm: src/wasmfx/imports_switch.wat
	$(WASM_INTERP_SWITCH) -d -i src/wasmfx/imports_switch.wat -o fiber_switch_wasmfx_imports.wasm

out/%_wasmfx.unopt.wasm: examples/%.c inc/fiber.h src/wasmfx/imports.wat src/wasmfx/wasmfx_impl.c fiber_wasmfx_imports.wasm | out
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_impl.c $(WASIFLAGS) $< -o $(@:.wasm=.pre.wasm)
	$(WASM_MERGE) fiber_wasmfx_imports.wasm "fiber_wasmfx_imports" $(@:.wasm=.pre.wasm) "main" -o $@
	chmod +x $@

out/%_wasmfx.wasm: out/%_wasmfx.unopt.wasm
	$(WASM_OPT) $< -o $@
	chmod +x $@

out/%_switch_wasmfx.wasm: examples/%_switch.c inc/fiber_switch.h src/wasmfx/imports_switch.wat src/wasmfx/wasmfx_switch_impl.c fiber_switch_wasmfx_imports.wasm | out
	$(WASICC) $(SHADOW_STACK_FLAG) -DWASMFX_CONT_SHADOW_STACK_SIZE=$(WASMFX_CONT_SHADOW_STACK_SIZE) -DWASMFX_CONT_TABLE_INITIAL_CAPACITY=$(WASMFX_CONT_TABLE_INITIAL_CAPACITY) -Wl,--export-table,--export-memory,--export=__stack_pointer src/wasmfx/wasmfx_switch_impl.c $(WASIFLAGS) $< -o $(@:.wasm=.pre.wasm)
	$(WASM_MERGE) fiber_switch_wasmfx_imports.wasm "fiber_switch_wasmfx_imports" $(@:.wasm=.pre.wasm) "main" -o $@
	chmod +x $@

out/%.cwasm: out/%.wasm
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
