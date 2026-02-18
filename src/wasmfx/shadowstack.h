#ifndef WASMFX_SHADOW_STACK_H
#define WASMFX_SHADOW_STACK_H

#include <stdint.h>

// Initialises the shadow stack for the continuation determined by
// `cont_index`.
void init_shadow_stack(uintptr_t cont_index);

// Resizes the vector of shadow stacks.
void change_shadow_stack_capacity(size_t new_capacity);

void free_shadow_stack(uintptr_t cont_index);
#endif
