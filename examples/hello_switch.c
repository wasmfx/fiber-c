// Cooperative printing of "hello world"
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fiber-switch.h>

static volatile fiber_t hello_fiber;
static volatile fiber_t world_fiber;

fiber_result_t status;

bool hello_done;
bool world_done;


void* hello(void *arg) {
  uint32_t i = (uint32_t)(uintptr_t)arg;

  static const char s[] = "hlowrd";

  if (!hello_done){
    while (i < strlen(s)) {
      putc(s[i], stdout);
      // printf("hello resumed with status %d\n", status);
      i = (uint32_t)(uintptr_t)fiber_switch(world_fiber, (void*)(uintptr_t)i, &status);
      if (status == FIBER_OK) hello_done = true;
    }
  }
  
  return NULL;
}

void* world(void *arg) {
  uint32_t i = (uint32_t)(uintptr_t)arg;
  static const char s[] = "el ol";
  printf("world resumed with status %d\n", status);

  if (!world_done) {
    putc(s[i], stdout);
    i++;
    i = (uint32_t)(uintptr_t)fiber_switch(hello_fiber, (void*)(uintptr_t)i, &status);
    if (status == FIBER_OK) world_done = true;
  }
  printf("world finished\n");

  return NULL;
}

int main(void) {
  fiber_init();

  hello_fiber = fiber_alloc(hello);
  world_fiber = fiber_alloc(world);

  hello_done = false;
  world_done = false;

  uint32_t i = 0;

  (void)fiber_resume(hello_fiber, (void*)(uintptr_t)i, &status);

  putc('\n', stdout);
  fflush(stdout);
  printf("main finished\n");

  fiber_free(hello_fiber);
  fiber_free(world_fiber);

  fiber_finalize();
  return 0;
}
