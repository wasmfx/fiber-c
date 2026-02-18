.globl wasmfx_ssptr_get
.globl wasmfx_ssptr_set

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

wasmfx_ssptr_get:
  .functype wasmfx_ssptr_get () -> (PTR)
  global.get __stack_pointer
end_function

wasmfx_ssptr_set:
  .functype wasmfx_ssptr_set (PTR) -> ()
  local.get 0
  global.set __stack_pointer
end_function
