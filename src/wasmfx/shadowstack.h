#ifndef WASMFX_SHADOW_STACK_H
#define WASMFX_SHADOW_STACK_H

#include <stdint.h>

// Runtime initialisation and finalisation.
void shadow_stack_runtime_init(size_t initial_capacity);
void shadow_stack_runtime_finalize(size_t current_capacity, size_t unused_capacity);

// Initialises the shadow stack for the continuation determined by
// `cont_index`.
void shadow_stack_init(uintptr_t cont_index);

// Frees a shadow stack segment
void shadow_stack_free(uintptr_t cont_index);

// Resizes the vector of shadow stacks.
void shadow_stack_change_capacity(size_t new_capacity);

// Save the current shadow stack for `cont_index`.
void shadow_stack_save(uintptr_t cont_index);

// Restores the shadow stack associated with `cont_index`.
void shadow_stack_restore(uintptr_t cont_index);
#endif
