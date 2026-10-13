// Iterative sum; an iterative variation of `treesum.c`
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <fiber.h>

#define PRINT_RESULTS 0

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
    fprintf(stderr, "Wrong number of arguments. Expected: 1");
    return -1;
  }
  fiber_init();

  int i = atoi(argv[1]);

  int32_t result = run(i);

  assert(result == (i * (i - 1)) / 2);

  #if PRINT_RESULTS
  printf("%d\n", result);
  #endif

  fiber_finalize();
  return 0;
}

#undef PRINT_RESULTS
