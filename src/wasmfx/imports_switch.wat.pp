(module $fiber_switch_wasmfx
  (rec
    (type $ft2 (func (param i32 (ref null $ct2)) (result i32)))
    (type $ft3 (func (param i32 i32 (ref null $ct2)) (result i32)))
    (type $ct2 (cont $ft2))
    (type $ct3 (cont $ft3)))
  (type $ft-initial (func (param i32 i32 i32) (result i32)))
  (type $ct-initial (cont $ft-initial))
  (type $ft2-generic (func (param i32 i32) (result i32)))
  (type $cancel-ft (func (result i32)))
  (type $cancel-ct (cont $cancel-ft))

  ;; We must make sure that there is only a single memory, so that our
  ;; load/store instructions act on the C heap, not a separate memory.
  (import "main" "memory" (memory $0 2))
  ;; This is created by clang to translate function pointers.
  (import "main" "__indirect_function_table" (table $indirect_function_table 0 funcref))

#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
  ;; The shadow stack pointer, created by clang
  (import "main" "__stack_pointer" (global $sstack_ptr (mut i32)))
#endif

  ;; The *address* where the global C variable sstack_current_ptrs is stored
  ;; in linear memory
  (global $sstack_current_ptrs_addr (mut i32) (i32.const 0))

  ;; Keeps track of the index, into the continuation table, of the "switched from" continuation
  (global $switched_from_global (mut i32) (i32.const 0))

  ;; Keeps track of the currently active continuation
  (global $active_continuation (mut i32) (i32.const 0))

  ;; Keep the initial size of this table in sync with INITIAL_TABLE_CAPACITY in
  ;; .c file.
  (table $conts WASMFX_CONT_TABLE_INITIAL_CAPACITY (ref null $ct2))


  (tag $yield (result i32))
  (tag $switch-return (param i32 i32))

  (func $grow_cont_table (export "wasmfx_grow_cont_table") (param $capacity_delta i32)
    (table.grow $conts (ref.null $ct2) (local.get $capacity_delta))
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
  (func $wasmfx_entry_trampoline (type $ft3)
    (table.set $conts (global.get $active_continuation) (local.get 2))
    (call_indirect $indirect_function_table (type $ft2-generic)
      (local.get 1)
      (global.get $active_continuation)
      (local.get 0)
    )
  )
  (func $initial_entry_trampoline
     (param $func_index i32)
     (param $argc i32)
     (param $argv i32)
     (result i32)

     (call_indirect $indirect_function_table (type $ft2-generic)
       (local.get $argc)
       (local.get $argv)
       (local.get $func_index))
  )
  (elem declare func $wasmfx_entry_trampoline $initial_entry_trampoline)


  (func $indexed_cont_new (export "wasmfx_indexed_cont_new")
    (param $func_index i32)
    (param $cont_index i32)
    (local $cont (ref $ct2))

    (local.get $func_index)
    (cont.new $ct3 (ref.func $wasmfx_entry_trampoline))
    (cont.bind $ct3 $ct2)
    (local.set $cont)

    (table.set $conts (local.get $cont_index) (local.get $cont))
  )

  (func $wasmfx_switch_trampoline (export "wasmfx_switch_trampoline")
    (param $func_index i32)
    (param $argc i32)
    (param $argv i32)
    (result i32)

    (local $arg i32)
    (local $old_shadow_sp i32)

    ;; Save shadow stack prior to invoking the initial trampoline
    (local.set $old_shadow_sp (global.get $sstack_ptr))

    ;; The initial continuation invocation is special as we pass argc
    ;; and argv to it.
    (block $done (result i32)
      (block $switch-return (result i32 i32 (ref $cancel-ct))
        (resume $ct-initial (on $yield switch) (on $switch-return $switch-return)
          (local.get $func_index)
          (local.get $argc)
          (local.get $argv)
          (cont.new $ct-initial (ref.func $initial_entry_trampoline)))
        ;; Returned
        (br $done)
      ) ;; $switch-return: [i32 i32 contref]
      (loop $keep-going (param i32 i32 (ref $cancel-ct)) (result i32)
        ;; TODO(dhil): clean-up resources
        (drop) ;; contref
        ;; Prepare next fiber
        (local.set $arg)
        (global.set $active_continuation)

        ;; Load the next shadow stack
#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
        ;; The following 5 instructions are equivalent to the following C code
        ;; (inlined here until we have wasm-opt):
        ;; __shadow_stack_ptr = sstack_current_ptrs[active_continuation]

        (i32.load (global.get $sstack_current_ptrs_addr))
        (i32.mul (i32.const 4) (global.get $active_continuation))
        (i32.add)
        (i32.load)
        (global.set $sstack_ptr)
#endif
        (block $switch-return (result i32 i32 (ref $cancel-ct))
          (resume $ct2 (on $yield switch) (on $switch-return $switch-return)
            (local.get $arg)
            (ref.null $ct2) ;; "dummy" continuation
            (table.get $conts (global.get $active_continuation)) ;; fetches the actual continuation object
          ) ;; we returned, stack is: [i32]
          (br $done)
        ) ;; $switch-return: [i32 i32 contref]
        (br $keep-going)
      ) ;; $keep-going: [i32]
    ) ;; $done: [i32]

    ;; Restore the original shadow stack segment
#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
    (global.set $sstack_ptr (local.get $old_shadow_sp))
#endif
  )

  (func $switch (export "wasmfx_switch")
    (param $target_index i32)
    (param $arg i32)
    (param $switched_from i32)
    (result i32)

    (local $self i32)
    (local $k (ref null $ct2))
    (local $old_shadow_sp i32)

    ;; Remember self
    (local.set $self (global.get $active_continuation))

    ;; Get the continuation object, and null-out its entry.
    (local.set $k (table.get $conts (local.get $target_index)))
    (table.set $conts (local.get $target_index) (ref.null $ct2))

    ;; Save shadow stack
#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
    ;; The following 5 instructions are equivalent to the following C code
    ;; (inlined here until we have wasm-opt):
    ;; sstack_current_ptrs[self] = __shadow_stack_ptr
    (i32.load (global.get $sstack_current_ptrs_addr))
    (i32.mul (i32.const 4) (local.get $self))
    (i32.add)
    (global.get $sstack_ptr)
    (i32.store)

    ;; The following 5 instructions are equivalent to the following C code
    ;; (inlined here until we have wasm-opt):
    ;; __shadow_stack_ptr = sstack_current_ptrs[target_index]
    (i32.load (global.get $sstack_current_ptrs_addr))
    (i32.mul (i32.const 4) (local.get $target_index))
    (i32.add)
    (i32.load)
    (global.set $sstack_ptr)
#endif

    ;; Switch to the continuation object
    (global.set $active_continuation (local.get $target_index))
    (global.set $switched_from_global (local.get $self))
    (switch $ct2 $yield (local.get $arg) (local.get $k))

    (local.set $k)
    ;; We came back from another continuation, stack is: [i32 contref]
    (table.set $conts (global.get $switched_from_global) (local.get $k))
    (i32.store (local.get $switched_from) (global.get $switched_from_global))

    ;; Restore shadow stack
#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
    (i32.load (global.get $sstack_current_ptrs_addr))
    (i32.mul (i32.const 4) (local.get $self))
    (i32.add)
    (i32.load)
    (global.set $sstack_ptr)
#endif

    (return)
  )

   (func $switch-return (export "wasmfx_switch_return")
    (param $target_index i32)
    (param $arg i32)

    (suspend $switch-return (local.get $target_index) (local.get $arg))
  )
)
