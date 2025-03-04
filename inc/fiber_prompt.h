/** A basic fiber interface. **/
#ifndef WASMFX_FIBER_C_H
#define WASMFX_FIBER_C_H

#include <stdint.h>

#define export(NAME) __attribute__((export_name(NAME)))

/** The abstract type of a prompt object **/
typedef uint32_t prompt_t;

/** The signature of a fiber entry point. **/
typedef void* (*fiber_entry_point_t)(void*, prompt_t);

/** The abstract type of a fiber object. **/
typedef struct fiber* fiber_t;

/** Allocates a new fiber with the default stack size. **/
export("fiber_alloc") fiber_t fiber_alloc(fiber_entry_point_t entry);

/** Reclaims the memory occupied by the fiber object. **/
export("fiber_free") void fiber_free(fiber_t fiber);

/** Yields control to the context of the provided prompt. This function must be
   called from within a fiber context. **/
export("fiber_yield_to") void* fiber_yield_to(void* arg, prompt_t prompt);

/** Possible status codes for `fiber_resume_with`. **/
typedef enum { FIBER_OK = 0, FIBER_YIELD = 1, FIBER_ERROR = 2 } fiber_result_t;

/** Resumes a given `fiber` with a freshly generated prompt and argument `arg`,
    returning some value of type `void*`. The output parameter `status`
   indicates whether the fiber ran to completion (`FIBER_OK`), yielded control
    (`FIBER_YIELD`), or failed (`FIBER_ERROR`), in the latter case the
    return value will always be `NULL`. **/
export("fiber_resume_with") void* fiber_resume_with(fiber_t fiber, void* arg,
                                                    fiber_result_t* status);

/** Initialises the fiber runtime. It must be called exactly once
    before using any of the other fiber_* functions. **/
export("fiber_init") void fiber_init(void);

/** Tears down the fiber runtime. It must be called after the final
    use of any of the other fiber_* functions. **/
export("fiber_finalize") void fiber_finalize(void);

#undef export
#endif
