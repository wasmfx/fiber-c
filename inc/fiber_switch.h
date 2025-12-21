/** A basic fiber interface. **/
#ifndef WASMFX_FIBER_C_H
#define WASMFX_FIBER_C_H

#define export(NAME) __attribute__((export_name(NAME)))

/** The signature of a fiber entry point. **/
typedef void* (*fiber_entry_point_t)(void*);

/** The abstract type of a fiber object. **/
typedef struct fiber* fiber_t;

/** Allocates a new fiber with the default stack size. **/
export("fiber_alloc")
fiber_t fiber_alloc(fiber_entry_point_t entry);

/** Reclaims the memory occupied by the fiber object. **/
export("fiber_free")
void fiber_free(fiber_t fiber);


/** Possible status codes for `fiber_switch`. **/
typedef enum { FIBER_OK = 0, FIBER_SWITCH = 1, FIBER_ERROR = 2 } fiber_result_t;


/** Switches to a given `fiber` with argument `arg`, returning some value
    of type `void*`. The output parameter `status` indicates whether
    the fiber ran to completion (`FIBER_OK`), yielded control
    (`FIBER_YIELD`), or failed (`FIBER_ERROR`), in the latter case the
    return value will be undefined. **/
export("fiber_switch")
void* fiber_switch(fiber_t fiber, void *arg, volatile fiber_t *switched_from);


/** Runs the provided `main` function in a fiber context. **/
export("fiber_main")
void *fiber_main(void *(*main)(void*), void* arg);

/** Gets the fiber running the main function of the user program. */
export("get_main_fiber")
fiber_t get_main_fiber(void);

#undef export
#endif
