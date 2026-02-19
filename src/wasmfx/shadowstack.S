.globl shadow_stack_runtime_pointer_init
.globl shadow_stack_save
.globl shadow_stack_restore

#ifdef __wasm64__
#define PTR i64
#define PTR_SIZE 8
#define ALIGN 3
#define PTRSTORE .int64
#else
#define PTR i32
#define PTR_SIZE 4
#define ALIGN 2
#define PTRSTORE .int32
#endif

// Import the memory
.import_module  __linear_memory, env
.import_name    __linear_memory, memory

.globaltype __stack_pointer, PTR
.globaltype sstack_current_ptrs_addr, PTR
sstack_current_ptrs_addr:

shadow_stack_save:
  .functype shadow_stack_save (PTR) -> ()
  global.get sstack_current_ptrs_addr
  PTR.load __linear_memory
  local.get 0 // the index
  PTR.const PTR_SIZE
  PTR.mul
  PTR.add
  global.get __stack_pointer
  PTR.store __linear_memory
end_function

shadow_stack_restore:
  .functype shadow_stack_restore (PTR) -> ()
  global.get sstack_current_ptrs_addr
  PTR.load __linear_memory
  local.get 0 // the index
  PTR.const PTR_SIZE
  PTR.mul
  PTR.add
  PTR.load __linear_memory
  global.set __stack_pointer
end_function

shadow_stack_runtime_pointer_init:
  .functype shadow_stack_runtime_pointer_init (i32) -> ()
  local.get 0
  global.set sstack_current_ptrs_addr
end_function
