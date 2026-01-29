// Cooperative printing of "hello world"
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fiber_switch.h>

static fiber_t hello_fiber;
static fiber_t world_fiber;

static bool hello_done;
static bool world_done;


void* hello(void *arg, fiber_t main_fiber) {
  uint32_t i = (uint32_t)(uintptr_t)arg;

  static const char s[] = "hlowrd";

  do  {
    putc(s[i], stdout);
    i = (uint32_t)(uintptr_t)fiber_switch(world_fiber, (void*)(uintptr_t)i, &hello_fiber);
  } while (!world_done && world_fiber != NULL);

  hello_done = true;
  fiber_switch_return(main_fiber, (void*)(uintptr_t)i);
  return NULL;
}

void* world(void *arg, fiber_t  __attribute__((unused))main_fiber) {
  uint32_t i = (uint32_t)(uintptr_t)arg;
  static const char s[] = "el ol";

  do {
    putc(s[i], stdout);
    i++;
    i = (uint32_t)(uintptr_t)fiber_switch(hello_fiber, (void*)(uintptr_t)i, &world_fiber);
  } while (i < strlen(s));

  world_done = true;
  fiber_switch(hello_fiber, (void*)(uintptr_t)i, &world_fiber);
  return NULL;
}

void *prog(void * __attribute__((unused))result, fiber_t dummy) {

  hello_fiber = fiber_alloc((fiber_entry_point_t)hello);
  world_fiber = fiber_alloc((fiber_entry_point_t)world);

  hello_done = false;
  world_done = false;

  uint32_t i = 0;

  // Initial switch must be from *some* fiber, so we use dummy.
  (void)fiber_switch(hello_fiber, (void*)(uintptr_t)i, &dummy);

  putc('\n', stdout);
  fflush(stdout);

  fiber_free(hello_fiber);
  fiber_free(world_fiber);

  return NULL;
}

int main(int __attribute__((unused)) argc, char * __attribute__((unused))argv[]) {

  void *result = fiber_main(prog, NULL);

  return (int)(intptr_t)result;
}
