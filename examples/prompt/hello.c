// Cooperative printing of "hello world"
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include <fiber/prompt.h>

void* hello(prompt_t p, void *arg) {
  static const char s[] = "hlowrd";
  uint32_t i = (uint32_t)(uintptr_t)arg;

  while (i < strlen(s)) {
    putc(s[i], stdout);
    yield_result_t res = fiber_yield_to(p, NULL);
    i = (uint32_t)(uintptr_t)res.value;
    p = res.prompt;
  }

  return NULL;
}

void* world(prompt_t p, void *arg) {
  static const char s[] = "el ol";
  uint32_t i = (uint32_t)(uintptr_t)arg;

  while (i < strlen(s)) {
    putc(s[i], stdout);
    yield_result_t res = fiber_yield_to(p, NULL);
    i = (uint32_t)(uintptr_t)res.value;
    p = res.prompt;
  }

  return NULL;
}

int prog(int __attribute__((unused)) argc, char** __attribute__((unused)) argv) {
  fiber_result_t status;
  fiber_t hello_fiber = fiber_alloc(hello);
  fiber_t world_fiber = fiber_alloc(world);

  bool hello_done = false;
  bool world_done = false;

  uint32_t i = 0;
  while (!hello_done && !world_done) {
    if (!hello_done) {
      (void)fiber_resume_with(hello_fiber, (void*)(uintptr_t)i, &status);
      assert(status != FIBER_ERROR);
      if (status == FIBER_OK) hello_done = true;
    }

    if (!world_done) {
      (void)fiber_resume_with(world_fiber, (void*)(uintptr_t)i, &status);
      assert(status != FIBER_ERROR);
      if (status == FIBER_OK) world_done = true;
    }
    i++;
  }

  putc('\n', stdout);
  fflush(stdout);

  fiber_free(hello_fiber);
  fiber_free(world_fiber);

  return 0;
}

int main(int argc, char** argv) {
  return fiber_main(prog, argc, argv);
}
