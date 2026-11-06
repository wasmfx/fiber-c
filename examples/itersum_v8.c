// Iterative sum; an iterative variation of `treesum.c`
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <fiber.h>


// Yields the natural numbers 0, 1, ... up to "arg"
void* range(void *arg) {
  int32_t max = (int32_t)(intptr_t)arg;
  for (int32_t i = 0; i < max; i++) {
    fiber_yield((void*)(intptr_t)i);
  }
  return NULL;
}

__attribute__((export_name("loop")))
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

__attribute__((export_name("init_loop")))
int init_loop() {
  fiber_init();
  return 10000000;
}

__attribute__((export_name("cleanup_loop")))
void cleanup_loop() {
  fiber_finalize();
}

int main() {
  int max = init_loop();

  int result = run(max);

  cleanup_loop();

  printf("%d\n", result);

  return 0;
}
