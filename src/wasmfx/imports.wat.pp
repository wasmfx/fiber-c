(module $fiber_wasmfx
  (type $ft1 (func (param i32) (result i32)))
  (type $ft2 (func (param i32 i32) (result i32)))
  (type $ct1 (cont $ft1))
  (type $ct2 (cont $ft2))

  ;; We must make sure that there is only a single memory, so that our
  ;; load/store instructions act on the C heap, not a separate memory.
  (import "main" "memory" (memory $0 2))
  ;; This is created by clang to translate function pointers.
  (import "main" "__indirect_function_table" (table $indirect_function_table 0 funcref))

#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
  ;; The shadow stack pointer, created by clang
  (import "main" "__exported_shadow_stack_pointer" (global $sstack_ptr (mut i32)))
#endif

  ;; The *address* where the global C variable sstack_current_ptrs is stored
  ;; in linear memory
  (global $sstack_current_ptrs_addr (mut i32) (i32.const 0))

  ;; Keep the initial size of this table in sync with INITIAL_TABLE_CAPACITY in
  ;; .c file.
  (table $conts WASMFX_CONT_TABLE_INITIAL_CAPACITY (ref null $ct1))


  (tag $yield (param i32) (result i32))

  (func $grow_cont_table (export "wasmfx_grow_cont_table") (param $capacity_delta i32)
    (table.grow $conts (ref.null $ct1) (local.get $capacity_delta))
    (drop)
  )

  ;; One-time initialization
  (func $wasmfx_fiber_init_wat (export "wasmfx_fiber_init_wat")
        (param $sstack_current_ptrs_addr i32)
    (global.set $sstack_current_ptrs_addr (local.get $sstack_current_ptrs_addr))
  )

  ;; This function is the entry point of all of our continuations.
  ;; clang translates function pointers into indices into the
  ;; `$indirect_function_table`, and the latter contains entries of type
  ;; `funcref`. There is no way to downcast from `funcref` to a concrete function
  ;; reference type. Thus we cannot call `cont.new` on entries from
  ;; `$indirect_function_table` directly, but must use this trampoline instead.
  (func $wasmfx_entry_trampoline (param $func_index i32) (param $arg i32) (result i32)
    (call_indirect $indirect_function_table (type $ft1)
      (local.get $arg)
      (local.get $func_index)
    )
  )
  (elem declare func $wasmfx_entry_trampoline)


  (func $indexed_cont_new (export "wasmfx_indexed_cont_new")
    (param $func_index i32)
    (param $cont_index i32)
    (local $cont (ref $ct1))

    (local.get $func_index)
    (cont.new $ct2 (ref.func $wasmfx_entry_trampoline))
    (cont.bind $ct2 $ct1)
    (local.set $cont)

    (table.set $conts (local.get $cont_index) (local.get $cont))
  )

  (func $indexed_resume (export "wasmfx_indexed_resume")
    (param $cont_index i32)
    (param $arg i32)
    (param $result_ptr i32)
    (result i32)
    (local $k (ref $ct1))
    (local $old_shadow_sp i32)

#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
    (local.set $old_shadow_sp (global.get $sstack_ptr))
    ;; The following 5 instructions are equivalent to the following C code
    ;; (inlined here until we have wasm-opt):
    ;; __shadow_stack_ptr = sstack_current_ptrs[cont_index]

    (i32.load (global.get $sstack_current_ptrs_addr))
    (i32.mul (i32.const 4) (local.get $cont_index))
    (i32.add)
    (i32.load)
    (global.set $sstack_ptr)
#endif

    (block $handler (result i32 (ref $ct1) )
      (block $on_error
        ;; Retrieve the continuation and test for null
        (local.set $k (br_on_null $on_error
           (table.get $conts (local.get $cont_index))))
        ;; resume the continuation
        (resume $ct1 (tag $yield $handler) (local.get $arg) (local.get $k))
        (i32.store (local.get $result_ptr) (i32.const 0)) ;; FIBER_OK
        (table.set $conts (local.get $cont_index) (ref.null $ct1))

#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
        ;; No need to save $sstack_ptr as continuation finished
        (global.set $sstack_ptr (local.get $old_shadow_sp))
#endif

        (return) ;; returns the value put on stack by resume
      ) ;; continuation is null
      (i32.store (local.get $result_ptr) (i32.const 2)) ;; FIBER_ERROR
      (return (i32.const -1))
    )
    (local.set $k)

    ;; stash continuation aside
    (table.set $conts (local.get $cont_index) (local.get $k))

    (i32.store (local.get $result_ptr) (i32.const 1)) ;; FIBER_YIELD

#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
    ;; The following 5 instructions are equivalent to the following C code
    ;; (inlined here until we have wasm-opt):
    ;; sstack_current_ptrs[cont_index] = __shadow_stack_ptr
    (i32.load (global.get $sstack_current_ptrs_addr))
    (i32.mul (i32.const 4) (local.get $cont_index))
    (i32.add)
    (global.get $sstack_ptr)
    (i32.store)

    (global.set $sstack_ptr (local.get $old_shadow_sp))
#endif

    ;; return suspend payload
    (return)
  )

  (func $suspend (export "wasmfx_suspend") (param $arg i32) (result i32)
    (suspend $yield (local.get $arg))
  )
)
