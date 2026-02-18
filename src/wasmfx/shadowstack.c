#ifdef FIBER_WASMFX_PRESERVE_SHADOW_STACK
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>

// Returns the current value of the Clang shadow stack pointer.
extern uintptr_t wasmfx_ssptr_get();

// Sets the Clang shadow stack pointer to `ptr_val`.
extern void wasmfx_ssptr_set(uintptr_t ptr_val);

// Fixed size of a shadow stack.
static const size_t cont_shadow_stack_size = WASMFX_CONT_SHADOW_STACK_SIZE;

// Given a table index i, `sstack_bottom_ptrs[i]` is the beginning of
// the shadow stack allocation of continuation i.  Invariant:
// sstack_bottom_ptrs has as many entries as `cont_table_capacity`
static void** sstack_bottom_ptrs;
// Given a table index i, `sstack_current_ptrs[i]` is the current
// stack pointer value of continuation i.  Invariant:
// sstack_current_ptrs has as many entries as `cont_table_capacity`
static void** sstack_current_ptrs;

// Initialises the shadow stack for the continuation determined by
// `cont_index`.
void init_shadow_stack(size_t cont_index) {
  char* shadow_stack_bottom = malloc(cont_shadow_stack_size);
  void* shadow_stack_usable_top =
    ((char*)shadow_stack_bottom) + cont_shadow_stack_size - 0x10;
  sstack_bottom_ptrs[cont_index] = shadow_stack_bottom;
  sstack_current_ptrs[cont_index] = shadow_stack_usable_top;
}

#else

// Noop implementation here

#endif


