// An asyncify implementation of the basic fiber interface.

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
// for printing things, remove later
#include <assert.h>

#include "fiber_switch.h"
#define import(NAME) __attribute__((import_module("asyncify"),import_name(NAME)))


/** Asyncify imports **/
// The following functions are asyncify primitives:
// * asyncify_start_unwind(iptr): initiates a continuation
//   capture. The argument `iptr` is a pointer to an asyncify stack.
// * asyncify_stop_unwind(): delimits a capture continuations.
// * asyncify_start_rewind(iptr): initiates a continuation
//   reinstatement. The argument `iptr` is a pointer to an asyncify
//   stack.
// * asyncfiy_stop_rewind(): delimits the extent of a continuation
//  reinstatement.
extern
import("start_unwind")
void asyncify_start_unwind (void*);

extern
import("stop_unwind")
void asyncify_stop_unwind(void);

extern
import("start_rewind")
void asyncify_start_rewind (void*);

extern
import("stop_rewind")
void asyncify_stop_rewind(void);

// The default stack size is 2MB.
static const size_t default_stack_size = ASYNCIFY_DEFAULT_STACK_SIZE;

// We track the currently active fiber via this global variable.
static volatile fiber_t active_fiber = NULL;
// The target fiber to switch to.
static volatile fiber_t target_fiber = NULL;
// The main fiber of the user program.
static volatile fiber_t main_fiber = NULL;

// Global variable tracking if we're in the very first switch
// static volatile bool first_switch = false;


// Fiber states:
// * ACTIVE: the fiber is actively executing.
// * YIELDING: the fiber is suspended.
// * RETURN_SWITCHING: the fiber is being switched from and destroyed.
// * DONE: the fiber is finished (i.e. run to completion).
typedef enum { ACTIVE, YIELDING, /**RETURN_SWITCHING,**/ DONE } fiber_state_t;

// A fiber stack is an asyncify stack, i.e. a reserved area of memory
// for asyncify to store the call chain and locals. Note: asyncify
// assumes `end` is at offset 4. Moreover, asyncify stacks grow
// upwards, so it must be that top <= end.
struct  __attribute__((packed)) fiber_stack {
  uint8_t *top;
  uint8_t *end;
  uint8_t *buffer;
};
static_assert(sizeof(uint8_t*) == 4, "sizeof(uint8_t*) != 4");
static_assert(sizeof(struct fiber_stack) == 12, "struct fiber_stack: No padding allowed");

// The fiber structure embeds the asyncify stack (struct fiber_stack),
// its state, an entry point, and two buffers for communicating
// payloads and managing fiber local data, respectively.
struct fiber {
  /** The underlying asyncify stack. */
  struct fiber_stack stack;
  // Fiber state.
  fiber_state_t state;
  // Initial function to run on the fiber.
  fiber_entry_point_t entry;
  // What this fiber switched from.
  fiber_t fiber_arg;
  // Payload buffer.
  void *arg;
};

// Allocates a fiber stack of size stack_size.
static struct fiber_stack fiber_stack_alloc(size_t stack_size) {
  uint8_t *buffer = malloc(sizeof(uint8_t) * stack_size);
  uint8_t *top = buffer;
  uint8_t *end = buffer + stack_size;
  struct fiber_stack stack = (struct fiber_stack) { top, end, /* NULL, */ buffer };
  return stack;
}

// Frees an allocated fiber_stack.
static void fiber_stack_free(struct fiber_stack fiber_stack) {
  free(fiber_stack.buffer);
}

#if defined STACK_POOL_SIZE && STACK_POOL_SIZE > 0
// Fiber stack pool
struct stack_pool {
  int32_t next;
  struct fiber_stack stacks[STACK_POOL_SIZE];
};

static struct fiber_stack stack_pool_next(volatile struct stack_pool *pool) {
  assert(pool->next >= 0 && pool->next < STACK_POOL_SIZE);
  return pool->stacks[pool->next++];
}

static void stack_pool_reclaim(volatile struct stack_pool *pool, struct fiber_stack stack) {
  assert(pool->next > 0 && pool->next <= STACK_POOL_SIZE);
  pool->stacks[--pool->next] = stack;
  return;
}

static volatile struct stack_pool pool;
#endif

// Allocates a fiber object.
// NOTE: the entry point `fn` should be careful about uses of `printf`
// and related functions, as they can cause asyncify to corrupt its
// own state. See `wasi-io.h` for asyncify-safe printing functions.
fiber_t fiber_sized_alloc(size_t stack_size, fiber_entry_point_t entry) {
  fiber_t fiber = (fiber_t)malloc(sizeof(struct fiber));
#if defined STACK_POOL_SIZE && STACK_POOL_SIZE > 0
  (void)stack_size;
  fiber->stack = stack_pool_next(&pool);
  // TODO(dhil): It may be necessary to reset the top pointer.  I'd
  // need to test on a larger example.
  fiber->stack.top = fiber->stack.buffer;
#else
  fiber->stack = fiber_stack_alloc(stack_size);
#endif
  fiber->state = ACTIVE;
  fiber->entry = entry;
  fiber->fiber_arg = NULL;
  fiber->arg = NULL;
  return fiber;
}

// Allocates a fiber object with the default stack size.
__attribute__((noinline))
fiber_t fiber_alloc(fiber_entry_point_t entry) {
  return fiber_sized_alloc(default_stack_size, entry);
}

// Frees a fiber object.
__attribute__((noinline))
void fiber_free(fiber_t fiber) {
#if defined STACK_POOL_SIZE && STACK_POOL_SIZE > 0
  stack_pool_reclaim(&pool, fiber->stack);
#else
  fiber_stack_free(fiber->stack);
#endif
  free(fiber);
}

__attribute__((noinline))
fiber_t get_main_fiber(void) {
  return main_fiber;
}

// Some checks we do on a target fiber before switching to it
static bool target_fiber_valid(fiber_t fiber) {
  // don't switch to a done or null fiber
  if (fiber->state == DONE || fiber == NULL) {
    printf("fiber_switch: error: switching to done or null fiber %p\n", (void*)fiber);
    return false;
  }

  // don't switch to yourself
  if (fiber == active_fiber) {
    printf("fiber_switch: error: switching to self %p\n", (void*)fiber);
    asyncify_start_unwind(&active_fiber->stack);
    return false;
  }

  return true;
}

__attribute__((noinline))
void* fiber_switch(fiber_t fiber, void *arg, volatile fiber_t * __attribute__((unused))switched_from) {

  if (!target_fiber_valid(fiber)) abort();
   
  if (active_fiber->state == ACTIVE) {
    // We are switching from this fiber to `fiber`.
    // Save `fiber` in a global such that we can retrieve it from the top-level.
    target_fiber = fiber;
    // Save payload on target fiber.
    target_fiber->arg = arg;
    target_fiber->fiber_arg = active_fiber;
    // Change fiber status.
    active_fiber->state = YIELDING;
    // Start unwinding.
    asyncify_start_unwind(&active_fiber->stack);
    return NULL;
  } else {
    // Otherwise we must be switched to
    asyncify_stop_rewind();
    active_fiber->state = ACTIVE;
    fiber = active_fiber->fiber_arg; 
    // Note(dhil): need to be a bit careful here to make sure `fiber` is correctly updated, probably needs to be a pointer-to-a-pointer to be correct.
    return active_fiber->arg;
  }
}

/** Switches to `target` and destroys currently executing `fiber`. **/
__attribute__((noinline))
void fiber_return_switch(fiber_t fiber, void *arg) {

  if (!target_fiber_valid(fiber)) abort();

  // We switch from this fiber to `fiber` and destroy it!
  // Start by doing the normal things
  target_fiber = fiber;
  // Save payload on target fiber.
  target_fiber->arg = arg;
  // Wipe the fiber arg for the target, since we're destroying it.
  target_fiber->fiber_arg = NULL;
  // We don't need to track RETURN_SWITCHING state for now
  // So we'll just change fiber status to YIELDING
  // active_fiber->state = RETURN_SWITCHING;
  active_fiber->state = YIELDING;
  // Start unwinding.
  asyncify_start_unwind(&active_fiber->stack);
}

// Noop when stack pooling is disabled.
void fiber_init(void) {
#if defined STACK_POOL_SIZE && STACK_POOL_SIZE > 0
  pool.next = STACK_POOL_SIZE;
  for (uint32_t i = 0; i < STACK_POOL_SIZE; i++) {
    stack_pool_reclaim(&pool, fiber_stack_alloc(default_stack_size));
  }
  assert(pool.next == 0);
#endif
}

// Noop when stack pooling is disabled.
void fiber_finalize(void) {
#if defined STACK_POOL_SIZE && STACK_POOL_SIZE > 0
  assert(pool.next == 0);
  for (uint32_t i = 0; i < STACK_POOL_SIZE; i++) {
    fiber_stack_free(stack_pool_next(&pool));
  }
  assert(pool.next == STACK_POOL_SIZE);
#endif
}

void *fiber_main(void *(*main)(void*, fiber_t), void* arg) {

  // Make sure the main function has been allocated a fiber
  assert(main != NULL);

  // Initialize fibers
  fiber_init();

  // Allocate the main fiber (running the initial function of our program)
  main_fiber = fiber_alloc(main);
  active_fiber = main_fiber;
  active_fiber->arg = arg;

  void *result = NULL;

  while (active_fiber->state == ACTIVE || target_fiber != NULL) {
    // Check whether we need to switch to a new fiber.
    if (target_fiber != NULL) {
      // We need to store the caller on the target, such that we can
      // retrieve it inside the target fiber.
      active_fiber = target_fiber;
    }

    // If the fiber was previously yielding then we need to rewind the
    // state.
    if (active_fiber->state == YIELDING) {
      asyncify_start_rewind(&active_fiber->stack);
    }

    // Run the fiber, including main_fiber as the second argument so that it can be accessed
    // by the user program.
    result = active_fiber->entry(active_fiber->arg,main_fiber);
    asyncify_stop_unwind();

    // If the active fiber isn't yielding at this point, it should be done
    if (active_fiber->state == YIELDING){
      // Prepare the target
      active_fiber = target_fiber;
    } 

      // We currently don't care about RETURN_SWITCHING but this might change!
      // Keeping this in here just in case.

      /**else if (active_fiber->state == RETURN_SWITCHING) {
      // Destroy the active fiber
      fiber_free(active_fiber);
      // Set the target
      active_fiber = target_fiber;
    } */

      else {
      active_fiber->state = DONE;
    }
    // If the target is also done, clear it so that we can exit the loop
    if (target_fiber->state == DONE) {
      target_fiber = NULL;
    }
  }

  // When no active fiber or target is done, we're finished
  fiber_free(main_fiber);
  fiber_finalize();
  return result;
}


#undef import
