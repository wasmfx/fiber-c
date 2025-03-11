// Cooperative printing of "hello world"
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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

static prompt_t global_prompt = 0;

void* world(prompt_t __attribute__((unused)) p, void *arg) {
  static const char s[] = "el ol";
  uint32_t i = (uint32_t)(uintptr_t)arg;

  while (i < strlen(s)) {
    putc(s[i], stdout);
    yield_result_t res = fiber_yield_to(global_prompt, NULL);
    i = (uint32_t)(uintptr_t)res.value;
    global_prompt = res.prompt;
  }

  return NULL;
}

void* indirection(prompt_t p, void* arg) {
  global_prompt = p;
  fiber_t f = fiber_alloc(world);
  fiber_result_t status;
  void* ans = fiber_resume_with(f, arg, &status);
  // TODO(dhil): When fiber_resume_with forwards, it eventually lands
  // here. We must not perform any side-effects between start_unwind
  // and stop_unwind. Internally, `assert` invokves printf, which
  // accesses memory, which in turn may corrupt the asyncify state.
  /* assert(status == FIBER_OK); */
  if (status != FIBER_OK && status != FIBER_FORWARD) {
    abort();
  }
  return ans;
}

int prog(int __attribute__((unused)) argc, char** __attribute__((unused)) argv) {
  fiber_result_t status;
  fiber_t hello_fiber = fiber_alloc(hello);
  fiber_t world_fiber = fiber_alloc(indirection);

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
