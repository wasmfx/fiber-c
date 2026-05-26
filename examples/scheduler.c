#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include <fiber.h>

// Parameters
#define PRINT_RESULTS 0
#define NUM_WORKERS 10
#define SWITCHES 10000000

// Array of workers
static fiber_t workers[NUM_WORKERS];

// Array of statuses
static bool worker_status[NUM_WORKERS];

// Array of results
static int32_t results[NUM_WORKERS];

void* increment(void *arg) {
  int32_t *result = (int32_t*)(intptr_t)arg;
  for (uint32_t i = 0; i < SWITCHES; ++i) {
    // Increment result
    (*result)++;
    (void)fiber_yield(NULL);
  }
  return NULL;
}

int main(void) {
  fiber_init();

  // Spawn workers.
  for (uint32_t i = 0; i < NUM_WORKERS; ++i) {
    workers[i] = fiber_alloc(increment);
  }
  // Initialize statuses
  for (uint32_t i = 0; i < NUM_WORKERS; ++i) {
    worker_status[i] = false;
  }

  // Scheduler
  bool keep_going = true;
  uint32_t next = 0;
  fiber_result_t status;
  do {
    (void)fiber_resume(workers[next], &results[next], &status);
    switch (status) {
    case FIBER_OK:
      worker_status[next] = true;
      break;
    case FIBER_YIELD:
      break;
    case FIBER_ERROR:
      abort(); // A fiber should never enter the error state.
      break;
    }

    // Find the next available worker.
    uint32_t i = 0;
    for (next = (next + 1) % NUM_WORKERS; i < NUM_WORKERS; ++i, next = (next+1) % NUM_WORKERS) {
      if (!worker_status[next]) {
        break;
      }
    }
    keep_going = i < NUM_WORKERS;
  } while (keep_going);

  #if PRINT_RESULTS
  for (uint32_t i = 0; i < NUM_WORKERS; ++i) {
    printf("%d\n", results[i]);
  }
  #endif

  // Clean up
  for (uint32_t i = 0; i < NUM_WORKERS; ++i) {
    fiber_free(workers[i]);
  }

  fiber_finalize();
}

#undef PRINT_RESULTS
#undef NUM_WORKERS
