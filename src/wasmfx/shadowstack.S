.globl wasmfx_ssptr_get
.globl wasmfx_ssptr_set
.globl wasmfx_ss_init

#ifdef __wasm64__
#define PTR i64
#define ALIGN 3
#define PTRSTORE .int64
#else
#define PTR i32
#define ALIGN 2
#define PTRSTORE .int32
#endif

.globaltype __stack_pointer, PTR
.globaltype sstack_current_ptrs_addr, PTR
sstack_current_ptrs_addr:

wasmfx_ssptr_get:
  .functype wasmfx_ssptr_get () -> (PTR)
  global.get __stack_pointer
end_function

wasmfx_ssptr_set:
  .functype wasmfx_ssptr_set (PTR) -> ()
  local.get 0
  global.set __stack_pointer
end_function

wasmfx_ss_init:
  .functype wasmfx_ss_init (i32) -> ()
  local.get 0
  global.set sstack_current_ptrs_addr
end_function
