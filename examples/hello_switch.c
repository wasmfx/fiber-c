// Cooperative printing of "hello world"
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fiber_switch.h>

static volatile fiber_t main_fiber;
static volatile fiber_t hello_fiber;
static volatile fiber_t world_fiber;

bool hello_done;
bool world_done;


void* hello(void *arg) {
  uint32_t i = (uint32_t)(uintptr_t)arg;
  
  static const char s[] = "hlowrd";

  while (!world_done) {
    putc(s[i], stdout);
    i = (uint32_t)(uintptr_t)fiber_switch(world_fiber, (void*)(uintptr_t)i, &hello_fiber);
  }

  hello_done = true;
  fiber_switch(main_fiber, (void*)(uintptr_t)i, &hello_fiber);
  return NULL;
}

void* world(void *arg) {
  uint32_t i = (uint32_t)(uintptr_t)arg;
  static const char s[] = "el ol";

  while (i < strlen(s)) {
    putc(s[i], stdout);
    i++;
    i = (uint32_t)(uintptr_t)fiber_switch(hello_fiber, (void*)(uintptr_t)i, &world_fiber);
  }
  world_done = true;
  fiber_switch(hello_fiber, (void*)(uintptr_t)i, &world_fiber);
  return NULL;
}

void *prog(void * __attribute__((unused))result) {

  hello_fiber = fiber_alloc(hello);
  world_fiber = fiber_alloc(world);
  main_fiber = get_main_fiber();

  hello_done = false;
  world_done = false;

  uint32_t i = 0;

  (void)fiber_switch(hello_fiber, (void*)(uintptr_t)i, &main_fiber);

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
