// Asynchronous workload simulation

#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

#include <fiber.h>

#define PRINT 0
#if PRINT
#include<inttypes.h>
#define maybe_printf(fmt, ...) printf(fmt __VA_OPT__(,) __VA_ARGS__)
#define maybe_printf0(fmt) printf(fmt)
#else
#define maybe_printf(fmt, ...)
#define maybe_printf0(fmt)
#endif

#define noinline __attribute__((noinline))

static const uint32_t total_conn = 10 * 1000000;
#define ACTIVE_CONN 10000U
static const uint32_t stack_kb = 32;

noinline void* as_stack_address(void* p) {
  return p;
}

noinline void* get_stack_top(void) {
  void* top = NULL;
  return as_stack_address(&top);
}

noinline uint32_t stack_use(long totalkb) {
  uint8_t* const sp = (uint8_t*)get_stack_top();
  size_t const page_size = 4096;
  size_t const total_pages = ((size_t)totalkb*1024 + page_size - 1) / page_size;
  uint32_t total = 0;
  for (size_t i = 0; i < total_pages; i++) {
    volatile uint8_t b = *(sp - (i * page_size));
    total += (uint32_t)b;
  }
  return total;
}

noinline void* async_worker(void *arg) {
  uint32_t const kb = (uint32_t)(uintptr_t)fiber_yield(arg);
  uint32_t volatile total = stack_use(kb);
  uint32_t volatile *alias = &total;
  return (void*)(uintptr_t)(*alias - total + 1);
}

noinline uint32_t async_wl(void) {
  maybe_printf0("async_test1M set up...\n");
  fiber_t *rs = (fiber_t*)malloc(sizeof(fiber_t) * ACTIVE_CONN);
  for (size_t i = 0; i < ACTIVE_CONN; i++) {
    rs[i] = fiber_alloc(async_worker);
  }

  maybe_printf("run %" PRIu32 "M connections with %" PRIu32 " active at a time, each using %" PRIu32 "kb stack...\n", total_conn / 1000000, ACTIVE_CONN, stack_kb);
  fiber_result_t status;
  uint32_t count = 0;
  for (size_t i = 0; i < total_conn; i++) {
    size_t const j = i % ACTIVE_CONN;

    uint32_t ans = (uint32_t)(uintptr_t)fiber_resume(rs[j], (void*)(uintptr_t)stack_kb, &status);
    assert(status != FIBER_ERROR && "no fiber should enter an error state");
    assert(ans == stack_kb && "every fiber should yield back its argument");

    // do the work
    ans = (uint32_t)(uintptr_t)fiber_resume(rs[j], (void*)(uintptr_t)stack_kb, &status);
    assert(status != FIBER_ERROR && "no fiber should enter an error state");
    count += ans;

    // Clean up and allocate new fiber.
    fiber_free(rs[j]);
    rs[j] = fiber_alloc(async_worker);
  }

  for (size_t j = 0; j < ACTIVE_CONN; j++) {
    uint32_t ans = (uint32_t)(uintptr_t)fiber_resume(rs[j], (void*)(uintptr_t)stack_kb, &status);
    assert(status != FIBER_ERROR && "no fiber should enter an error state");
    assert(ans == stack_kb && "every fiber should yield back its argument");

    ans = (uint32_t)(uintptr_t)fiber_resume(rs[j], (void*)(uintptr_t)stack_kb, &status);
    assert(status != FIBER_ERROR && "no fiber should enter an error state");
    count += ans;

    fiber_free(rs[j]);
  }
  free(rs);

  __attribute__((unused)) double total_mb = (double)(total_conn * stack_kb) / 1024.0;
  maybe_printf("total stack used: %.3fmb, count=%" PRIu32 "\n", total_mb, count);

  return count;
}

int main(void) {
  fiber_init();
  uint32_t const result = async_wl();
  assert(result == 10010000 && "result validation failed");
  fiber_finalize();
  return 0;
}

#undef maybe_print
#undef maybe_print0
#undef PRINT
#undef ACTIVE_CONN
#undef noinline
