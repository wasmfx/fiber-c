#include <assert.h>
#include <stdint.h>
#include <stdlib.h>

#include <shadowstack.h>

extern void wasmfx_ss_init(void *sstack_current_ptrs_addr);

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
void init_shadow_stack(uintptr_t cont_index) {
  char* shadow_stack_bottom = malloc(cont_shadow_stack_size);
  void* shadow_stack_usable_top =
    ((char*)shadow_stack_bottom) + cont_shadow_stack_size - 0x10;
  sstack_bottom_ptrs[(size_t)cont_index] = shadow_stack_bottom;
  sstack_current_ptrs[(size_t)cont_index] = shadow_stack_usable_top;
}


void change_shadow_stack_capacity(size_t new_capacity) {
   sstack_bottom_ptrs = realloc(sstack_bottom_ptrs, sizeof(void*) * new_capacity);
   sstack_current_ptrs = realloc(sstack_current_ptrs, sizeof(void*) * new_capacity);
}

void free_shadow_stack(uintptr_t cont_index) {
  void* shadow_stack_usable_top =
    ((char*)sstack_bottom_ptrs[(size_t)cont_index]) + cont_shadow_stack_size - 0x10;
  sstack_current_ptrs[(size_t)cont_index] = shadow_stack_usable_top;
}

void init_shadow_stack_runtime(size_t initial_capacity) {
  wasmfx_ss_init(&sstack_current_ptrs);
  sstack_bottom_ptrs = malloc(initial_capacity * sizeof(void*));
  sstack_current_ptrs = malloc(initial_capacity * sizeof(void*));
}

void finalize_shadow_stack_runtime(size_t current_capacity, size_t unused_capacity) {
  assert(unused_capacity < current_capacity);
  for (size_t i = 0; i < current_capacity - unused_capacity; i++) {
    free(sstack_bottom_ptrs[i]);
  }
  free(sstack_bottom_ptrs);
  free(sstack_current_ptrs);
}
