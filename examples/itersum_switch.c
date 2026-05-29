// Iterative sum; an iterative variation of `treesum.c`
// Now using `switch`!
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <fiber_switch.h>

#define PRINT_RESULTS 0

void* sum(void *arg, fiber_t caller) {
  assert(caller != NULL);
  int32_t const max = (int32_t)(intptr_t)arg;
  for (int32_t i = 0; i < max; i++) {
    fiber_switch(caller, (void*)(intptr_t)i, &caller);
  }
  fiber_switch_return(caller, NULL);
  return NULL;
}

void* run(void *arg, fiber_t caller) {
  // assert(caller != NULL);
  fiber_t sum_fiber = fiber_alloc(sum);
  int32_t result = 0, i = 0;
  int32_t const max = (int32_t)(intptr_t)arg;

  int32_t val = (int32_t)(intptr_t)fiber_switch(sum_fiber, (void*)(intptr_t)max, &sum_fiber);

  while (i++ < max) {
    result += (int32_t)(intptr_t)val;
    val = (int32_t)(intptr_t)fiber_switch(sum_fiber, NULL, &sum_fiber);
  }

  fiber_free(sum_fiber);
  fiber_switch_return(caller, (void*)(intptr_t)result);
  return NULL;
}

void *prog(int argc, char **argv) {

  fiber_t run_fiber = fiber_alloc(run);

  if (argc != 2) {
    fprintf(stderr, "Wrong number of arguments. Expected: 1");
    return 0;
  }

  int const i = atoi(argv[1]);
  int32_t result = (int32_t)(intptr_t)fiber_switch(run_fiber, (void*)(intptr_t)i, &run_fiber);
  assert(result == (i * (i - 1)) / 2);

  #if PRINT_RESULTS
  printf("%d\n", result);
  #endif

  fiber_free(run_fiber);

  return 0;
}

int main(int argc, char** argv) {

  fiber_main(prog, argc, argv);

  return 0;
}

#undef PRINT_RESULTS
