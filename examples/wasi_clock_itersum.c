// Iterative sum; an iterative variation of `treesum.c`
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <fiber.h>
#include <wasi/api.h>

#include "wasi_clock_params.h"


// Yields the natural numbers 0, 1, ... up to "arg"
void* range(void *arg) {
  int32_t max = (int32_t)(intptr_t)arg;
  for (int32_t i = 0; i < max; i++) {
    fiber_yield((void*)(intptr_t)i);
  }
  return NULL;
}

int32_t run(int32_t max) {
  fiber_result_t status;
  fiber_t gen = fiber_alloc(range);
  int32_t result = 0, i = 0;

  void* val = fiber_resume(gen, (void*)(intptr_t)max, &status);

  while (status == FIBER_YIELD && i++ < max) {
    result += (int32_t)(intptr_t)val;
    val = fiber_resume(gen, NULL, &status);
  }

  fiber_free(gen);
  return result;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        fprintf(stderr, "Wrong number of arguments. Expected: 1\n");
        return -1;
    }

    fiber_init();

    int i = atoi(argv[1]);

    // Do 3 warmup runs of the main loop:
    for (int j = 0; j < WARMUP_RUNS; j++) {
        int32_t result = run(i);
        printf("Doing warmup run %d/%d, result: %d\n", j + 1, WARMUP_RUNS, result);
    }

    // Start timing
    __wasi_timestamp_t start, end;
    __wasi_errno_t clock_status;

    for (int j = 0; j < RUNS; j++) {
      clock_status = __wasi_clock_time_get(
          __WASI_CLOCKID_MONOTONIC,
          1,
          &start
      );

      // Timed code
      run(i);
      // End timed code

      clock_status = __wasi_clock_time_get(
          __WASI_CLOCKID_MONOTONIC,
          1,
          &end
      );

      uint64_t elapsed_ns = end - start;
      assert(clock_status == 0 && "clock_time_get failed");
      printf("Execution time:%llu\n",
            (unsigned long long)elapsed_ns);
    }

    fiber_finalize();

    return 0;
}