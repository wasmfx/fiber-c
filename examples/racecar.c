// Cooperative printing of "racecar"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fiber_switch.h>

static volatile fiber_t main_fiber;
static volatile fiber_t rr;
static volatile fiber_t cc;
static volatile fiber_t aa;
static volatile fiber_t e;

void* rr_func(void *__attribute__((unused))arg, fiber_t main_fiber) {
  putc('r', stdout);
  fiber_switch(aa, NULL, &rr);
  putc('r', stdout);
  fiber_switch_return(main_fiber, NULL);
  return NULL;
}

void* aa_func(void *__attribute__((unused))arg, fiber_t  __attribute__((unused))dummy) {
  putc('a', stdout);
  fiber_switch(cc, NULL, &aa);
  putc('a', stdout);
  fiber_switch_return(rr, NULL);
  return NULL;
}

void* cc_func(void *__attribute__((unused))arg, fiber_t  __attribute__((unused))dummy) {
  putc('c', stdout);
  fiber_switch(e, NULL, &cc);
  putc('c', stdout);
  fiber_switch_return(aa, NULL);
  return NULL;
}

void* e_func(void *__attribute__((unused))arg, fiber_t  __attribute__((unused))dummy) {
  putc('e', stdout);
  fiber_switch_return(cc, NULL);
  return NULL;
}

void *prog(void * __attribute__((unused))result, fiber_t  __attribute__((unused))dummy) {

    rr = fiber_alloc(rr_func);
    aa = fiber_alloc(aa_func);
    cc = fiber_alloc(cc_func);
    e = fiber_alloc(e_func);

    (void)fiber_switch(rr, NULL, &main_fiber);

    putc('\n', stdout);
    fflush(stdout);

    return NULL;
}

int main(int __attribute__((unused)) argc, char * __attribute__((unused))argv[]) {

  void *result = fiber_main(prog, NULL);

  return (int)(intptr_t)result;
}
