/** A basic fiber interface. **/
#ifdef WASMFX_FIBER_C_H
#error "the prompt implementation conflicts with the standard implementation"
#endif
#ifndef WASMFX_FIBER_C_PROMPT_H
#define WASMFX_FIBER_C_PROMPT_H

#define export(NAME) __attribute__((export_name(NAME)))

#include <stdint.h>

/** Type of a prompt. **/
typedef uint32_t prompt_t;

/** The result type of a yield. **/
typedef struct yield_result {
  prompt_t prompt;
  void* value;
} yield_result_t;

/** The signature of a fiber entry point. **/
typedef void* (*fiber_entry_point_t)(prompt_t, void*);

/** The abstract type of a fiber object. **/
typedef struct fiber* fiber_t;

/** Allocates a new fiber with the default stack size. **/
export("fiber_alloc")
fiber_t fiber_alloc(fiber_entry_point_t entry);

/** Reclaims the memory occupied by the fiber object. **/
export("fiber_free")
void fiber_free(fiber_t fiber);

/** Yields control to the context of the provided prompt. This
    function must be called from within a fiber context. **/
export("fiber_yield_to")
yield_result_t fiber_yield_to(prompt_t p, void *arg);

/** Possible status codes for `fiber_resume`. **/
typedef enum { FIBER_OK = 0, FIBER_YIELD = 1, FIBER_ERROR = 2, FIBER_FORWARD = 3 } fiber_result_t;

/** Resumes a given `fiber` with argument `arg`, returning some value
    of type `void*`. The output parameter `status` indicates whether
    the fiber ran to completion (`FIBER_OK`), yielded control
    (`FIBER_YIELD`), or failed (`FIBER_ERROR`), in the latter case the
    return value will always be `NULL`. **/
export("fiber_resume_with")
void* fiber_resume_with(fiber_t fiber, void *arg, fiber_result_t *status);


/** Runs the provided `main` function in a fiber context. **/
export("fiber_main")
int fiber_main(int (*main)(int,char**), int, char**);

#undef export
#endif
