/** A basic fiber interface. **/
#ifndef WASMFX_FIBER_C_H
#define WASMFX_FIBER_C_H

#define export(NAME) __attribute__((export_name(NAME)))
#define __wasm_import__(MODULE, NAME) __attribute__((import_module(MODULE),import_name(NAME)))
#define __wasm_export__(NAME) __attribute__((export_name(NAME)))


/** The signature of a fiber entry point. **/
typedef void* (*fiber_entry_point_t)(void*);

/** The abstract type of a fiber object. **/
typedef struct fiber* fiber_t;

/** Allocates a new fiber with the default stack size. **/
export("fiber_alloc")
fiber_t fiber_alloc(fiber_entry_point_t entry);

/** Reclaims the memory occupied by a fiber object. **/
export("fiber_free")
void fiber_free(fiber_t fiber);

/** Yields control to its parent context. This function must be called
    from within a fiber context. **/
export("fiber_yield")
void* fiber_yield(void *arg);

/** Possible status codes for `fiber_resume`. **/
typedef enum { FIBER_OK = 0, FIBER_YIELD = 1, FIBER_ERROR = 2 } fiber_result_t;

/** Resumes a given `fiber` with argument `arg`. **/
export("fiber_resume")
void* fiber_resume(fiber_t fiber, void *arg, fiber_result_t *result);


/** Initializes fiber support. Must be called exactly once before using any of
    the other fiber_* functions. **/
export("fiber_init")
void fiber_init(void);

/** Un-initializes fiber support. If fiber_initialize has ever beed called, then
    fiber_uninitialize must called prior to exiting the program. **/
export("fiber_finalize")
void fiber_finalize(void);

#undef export
#endif
