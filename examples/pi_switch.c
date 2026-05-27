// Monte Carlo PI estimation

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>

#include <fiber_switch.h>

// Parameters
#define PRINT_RESULTS 0
#define NUM_TASKS 1000
// Number of samples taken between yields.
static uint32_t const BATCH_SIZE = 100000;
// Number of batches to run in total. Each fiber will take YIELDS * BATCH_SIZE samples
static uint32_t const YIELDS = 50;

// Global state for scheduler
bool keep_going = true;
uint32_t next = 0;

// Array of results
static double results[NUM_TASKS];

// Array of workers
static fiber_t workers[NUM_TASKS];

// Array of statuses
static bool worker_status[NUM_TASKS];

// Cache main loop
fiber_t main_fiber;

void update_state() { 
  // Update global variable `next` to point to the next available worker (if any).
  uint32_t i = 0;
  for (next = (next + 1) % NUM_TASKS; i < NUM_TASKS; ++i, next = (next+1) % NUM_TASKS) {
    if (!worker_status[next]) {
      break;
    }
  }
  // Update keep_going variable too
  keep_going = i < NUM_TASKS - 1;
}

void scheduler(bool worker_done, fiber_t caller) { 
  if (worker_done) {
    // Mark the current worker as done.
    worker_status[next] = true;
    // Determine whether we should keep going.
    update_state();
    if (!keep_going) {
      // If no more available workers, switch-return to the outer loop.     
      fiber_switch_return(main_fiber, NULL);
    } else {
      // If the current worker is done, switch-return to the next available worker.
      fiber_switch_return(workers[next], &results[next]);
    }    
  }
  // Otherwise, simply switch onto the next available worker.
  update_state();
  fiber_switch(workers[next],&results[next],&caller); 
}

void* monte_carlo(void *arg, fiber_t caller) {
  double *pi = (double*)(intptr_t)arg;
  double inside = 0;
  double total = 0;

  // Save reference to main loop if this is the first entry to the first worker
  if (next == 0) { main_fiber = caller; }

  for (uint32_t i = 0; i < YIELDS; ++i) {
    for (uint32_t j = 0; j < BATCH_SIZE; ++j) {
      double const x = (double)rand() / ((double)RAND_MAX + 1);
      double const y = (double)rand() / ((double)RAND_MAX + 1);
      double const dist = x * x + y * y;

      if (fabs(dist - 1.0) < 0.0000000001 || dist < 1.0) {
        inside += 1.0;
      }

      total += 1.0;
    }
  scheduler(false, caller);
  }

  *pi = (4.0 * inside) / total;
  scheduler(true, caller);
  // unreachable
  return NULL;
}

void *prog(int __attribute__((unused)) argc, char __attribute__((unused)) **argv) {
  // Initialize with fixed seed for deterministic runs
  srand(0xC0FFEE);

  // Spawn workers.
  for (uint32_t i = 0; i < NUM_TASKS; ++i) {
    workers[i] = fiber_alloc(monte_carlo);
  }

  // Initialize statuses
  for (uint32_t i = 0; i < NUM_TASKS; ++i) {
    worker_status[i] = false;
  }

  // Switch onto the initial worker
  fiber_switch(workers[0], &results[0], &workers[0]);
  
  return NULL;
}

int main(int argc, char **argv) {

  fiber_main(prog, argc, argv);
  
  #if PRINT_RESULTS
  for (uint32_t i = 0; i < NUM_TASKS; ++i) {
    printf("%f\n", results[i]);
  }
  #endif

  // Validate results and clean up
  for (uint32_t i = 0; i < NUM_TASKS; ++i) {
    assert(results[i] > 0.0 && "Result should be positive");
    fiber_free(workers[i]);
  }

  return 0;
}

#undef PRINT_RESULTS
#undef NUM_TASKS