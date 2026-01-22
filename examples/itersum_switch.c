// Iterative sum; an iterative variation of `treesum.c`
// Now using `switch`!
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <fiber_switch.h>

static fiber_t run_fiber;
static fiber_t sum_fiber;

static int prog_argc;
static char** prog_argv;


void* sum(void *arg, fiber_t  __attribute__((unused))main_fiber) {
  int32_t max = (int32_t)(intptr_t)arg;
  for (int32_t i = 0; i < max; i++) {
    fiber_switch(run_fiber, (void*)(intptr_t)i, &sum_fiber);
  }
  fiber_return_switch(run_fiber, NULL);
  return NULL;
}

int32_t run(int32_t max, fiber_t main_fiber) {

  sum_fiber = fiber_alloc((fiber_entry_point_t)sum);
  int32_t result = 0, i = 0;


  void* val = fiber_switch(sum_fiber, (void*)(intptr_t)max, &run_fiber);

  while (i++ < max) {
    result += (int32_t)(intptr_t)val;
    val = fiber_switch(sum_fiber, NULL, &run_fiber);
  }

  fiber_free(sum_fiber);
  fiber_return_switch(main_fiber, (void*)(intptr_t)result);
  return 0;
}

void *prog(void * __attribute__((unused))unused_result, fiber_t dummy) {

  run_fiber = fiber_alloc((fiber_entry_point_t)run);

  if (prog_argc != 2) {
    fprintf(stderr, "Wrong number of arguments. Expected: 1");
    return 0;
  }

  int i = atoi(prog_argv[1]);

  int32_t result = (int32_t)fiber_switch(run_fiber, (void*)(intptr_t)i, &dummy);
  
  printf("%d\n", result);

  fiber_free(run_fiber);

  return 0;
}

int main(int argc, char** argv) {

  prog_argc = argc;
  prog_argv = argv;

  void *result = fiber_main(prog, NULL);
  
  return (int)(intptr_t)result;
}
