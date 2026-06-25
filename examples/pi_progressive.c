// This is a fun, concurrently progressive approximation of pi using the Monte
// Carlo method. It spawns a bunch of fibers, each of which gets to work
// sampling points that are observations toward an estimate of pi. Periodically
// each fiber yields and the main function prints the current estimate by
// combining all the observations.
//
// This could be a reasonable approach to a large monte-carlo simulation where
// you wanted to use parallel computation to get the answer faster. Of course in
// our setting the actual execution will be single-threaded, but it's still an
// interesting example program.
//
// The estimates are printed at each yield point, so you can watch the estimate
// converge.

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include <fiber.h>

// Parameters
#define PRINT_RESULTS 0
#define NUM_TASKS 1000
static uint32_t const BATCH_SIZE = 100000;
static uint32_t const YIELDS = 50;

// Array of workers
static fiber_t workers[NUM_TASKS];

// Array of statuses
static bool worker_status[NUM_TASKS];

struct result {
  double inside;
  double total;
};

void* monte_carlo(struct result *arg) {

  for (uint32_t i = 0; i < YIELDS; ++i) {
    for (uint32_t j = 0; j < BATCH_SIZE; ++j) {
      double const x = (double)rand() / ((double)RAND_MAX + 1);
      double const y = (double)rand() / ((double)RAND_MAX + 1);

      double const dist = x * x + y * y;

      if (fabs(dist - 1.0) < 0.0000000001 || dist < 1.0) {
        arg->inside += 1.0;
      }

      arg->total += 1.0;
    }

    (void)fiber_yield(NULL);
  }

  return NULL;
}

int main(void) {
  fiber_init();

  // Initialize with fixed seed for deterministic runs
  srand(0xC0FFEE);

  // Spawn workers.
  for (uint32_t i = 0; i < NUM_TASKS; ++i) {
    workers[i] = fiber_alloc((fiber_entry_point_t)monte_carlo);
  }
  // Initialize statuses
  for (uint32_t i = 0; i < NUM_TASKS; ++i) {
    worker_status[i] = false;
  }

  // Array of results
  static struct result results[NUM_TASKS];

  // Scheduler
  bool keep_going = true;
  uint32_t next = 0;
  fiber_result_t status;
  double pi_estimate = 3; // As everyone knows, pi is approximately 3, so this is a reasonable initial estimate.

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
    double inside = 0;
    double total = 0;
    for (int i=0; i < NUM_TASKS; ++i) {
      inside += results[i].inside;
      total += results[i].total;
    }
    pi_estimate = (4.0 * inside) / total;

#if PRINT_RESULTS
    // Print the current estimate.
    printf("%f\n", pi_estimate);
#endif

    // Find the next available worker.
    uint32_t i = 0;
    for (next = (next + 1) % NUM_TASKS; i < NUM_TASKS; ++i, next = (next+1) % NUM_TASKS) {
      if (!worker_status[next]) {
        break;
      }
    }
    keep_going = i < NUM_TASKS;
  } while (keep_going);

  printf("%f\n", pi_estimate);
  assert(fabs(pi_estimate - 3.14159265359) < 0.0001 && "wrong result");

  // Clean up
  for (uint32_t i = 0; i < NUM_TASKS; ++i) {
    fiber_free(workers[i]);
  }

  fiber_finalize();
}
#undef PRINT_RESULTS
#undef NUM_TASKS
