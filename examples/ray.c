#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "fiber.h"
#include "math.h"

#define min(x, y) ( (x) < (y) ? (x) : (y) )
#define max(x, y) ( (x) >= (y) ? (x) : (y) )

#define WIDTH 600
#define HEIGHT 600
static char BUFFER[4 * HEIGHT * WIDTH] = {0};

#define export(NAME) __attribute__((export_name(NAME)))

struct pt {
    float x, y, z;
};

const struct pt viewpoint =  {0, 3, 0};
const struct pt cameraAngle =  {0, 0, 1};
const struct pt planenormal =  {0, 1, 0};

//const
struct pt sphereCenter =  {-1, 1, 70};
const float sphereRadius = 1;

const struct pt lightSource = {10, 20, 0};

float
dot(const struct pt *a, const struct pt *b)
{
    return a->x * b->x + a->y * b->y + a->z * b->z;
}

void
scaleOut(const struct pt *a, float n, const struct pt *v, struct pt *result)
{
    result->x = a->x + n * v->x;
    result->y = a->y + n * v->y;
    result->z = a->z + n * v->z;
}

void
normalize(struct pt *v)
{
    float size = sqrt(dot(v, v));
    v->x = v->x / size;
    v->y = v->y / size;
    v->z = v->z / size;
}

int
planeHit(const struct pt *viewpoint, const struct pt *viewdir, const struct pt *planenormal, struct pt *result)
{
    float n = -dot(viewpoint, planenormal) / dot(viewdir, planenormal);
    if (n > 0) {
        result->x = viewpoint->x + n * viewdir->x;
        result->y = viewpoint->y + n * viewdir->y;
        result->z = viewpoint->z + n * viewdir->z;
        return 1;
    } else {
        result->x = 0;
        result->y = 0;
        result->z = 0;
        return 0;
    }
}

void
diff(const struct pt *a, const struct pt *b, struct pt *result)
{
    result->x = a->x - b->x;
    result->y = a->y - b->y;
    result->z = a->z - b->z;
}

int
sphereHit(const struct pt *viewpoint, const struct pt *viewdir, const struct pt *sphereCenter, float radius, struct pt *result) {
    float a = dot(viewdir, viewdir);
    float b = 2 * dot(viewpoint, viewdir) - 2 * dot(viewdir, sphereCenter);
    float c = dot(viewpoint, viewpoint) + dot(sphereCenter, sphereCenter) - 2 * dot(viewpoint, sphereCenter) - radius * radius;
    float discrim = b * b - 4 * a * c;
    if (discrim < 0) return 0;
    float npos = (-b + sqrt(b * b - 4 * a * c)) / 2 * a;
    float nneg = (-b - sqrt(b * b - 4 * a * c)) / 2 * a;
    if (nneg <= 0 && npos <= 0) return 0;
    float n;
    if (nneg < 0) {
        n = npos;
    }
    if (npos < 0) {
        n = nneg;
    }
    if (nneg > 0 && npos > 0) {
        n = min(nneg, npos);
    };
    scaleOut(viewpoint, n, viewdir, result);
    return 1;
}

void
setPixel(char *buffer, int width, int i, int j, char alpha, char blue, char green, char red)
{
    buffer[4 * (i*width + j) + 0] = red;
    buffer[4 * (i*width + j) + 1] = green;
    buffer[4 * (i*width + j) + 2] = blue;
    buffer[4 * (i*width + j) + 3] = alpha;
}

export("getBuffer")
char *
getBuffer() {
    return BUFFER;
}

export("render")
int
render(int time) {
    sphereCenter.z = 0 + time;
    for (int i = 0; i < HEIGHT; i++){
        for (int j = 0; j < WIDTH; j++){
            struct pt ray = {
                // Note: distorted, not normalized.
                ((float)j/WIDTH - 0.5) * 0.2,
                -((float)i/HEIGHT - 0.5) * 0.2,
                1,
            };

            struct pt hitPt;

            if (sphereHit(&viewpoint, &ray, &sphereCenter, sphereRadius, &hitPt)) {
                struct pt sphereVector;
                struct pt lightVector;
                diff(&hitPt, &sphereCenter, &sphereVector);
                normalize(&sphereVector);
                diff(&lightSource, &sphereCenter, &lightVector);
                normalize(&lightVector);
                float incidence = dot(&sphereVector, &lightVector);
                incidence = max(incidence, 0);
                setPixel(BUFFER, WIDTH, i, j, 0xFF, 0xFF * incidence, 0x00, 0x7F * incidence + 0x80);
                continue;
            }
            if (planeHit(&viewpoint, &ray, &planenormal, &hitPt)) {
                char value;
                if (((int)(floor(hitPt.x / 1.0)) + (int)(floor(hitPt.z / 1.0))) % 2) {
                    value = 0xFF;
                } else {
                    value = 0x00;
                }
                setPixel(BUFFER, WIDTH, i, j, 0xFF, value, value, 0xFF);
            } else {
                setPixel(BUFFER, WIDTH, i, j, 0xFF, 0x00, 0xA0, 0xFF);
            }
        }
    }
    return 747;
}

void *
render_stub(void *arg) {
    int time = (int)(intptr_t)arg;
    render(time);
    return NULL;
}

#define MAX_TASKS 800

// Array of workers
static fiber_t workers[MAX_TASKS];

// Array of statuses
static bool fiber_ready[MAX_TASKS];
static bool fiber_allocated[MAX_TASKS];
static void *fiber_arg[MAX_TASKS];

void
scheduler_init() {
  fiber_init();
  for (uint32_t i = 0; i < MAX_TASKS; ++i) {
    fiber_ready[i] = false;
  }
}

void
scheduler_loop() {
  bool keep_going = true;
  uint32_t next = 0;
  fiber_result_t status;
  do {
    if (!fiber_allocated[next] || !fiber_ready[next]) {
      return;
    }
    (void)fiber_resume(workers[next], fiber_arg[next], &status);
    fiber_arg[next] = NULL;  // The arg only gets passed to the starting function; clear it afterwards.
    switch (status) {
    case FIBER_OK:
      fiber_ready[next] = false;
      fiber_allocated[next] = false;
      break;
    case FIBER_YIELD:
      fiber_ready[next] = true;
      break;
    case FIBER_ERROR:
      abort(); // A fiber should never enter the error state.
      break;
    }

    // Find a ready fiber.
    // `next` tracks the identity of the fiber.
    // i counts the number of fibers checked; since `next` wraps around the array,
    // we use i to ensure we just check each fiber once.
    uint32_t i = 0;
    for (next = (next + 1) % MAX_TASKS; i < MAX_TASKS; ++i, next = (next+1) % MAX_TASKS) {
      if (fiber_allocated[next] && fiber_ready[next]) {
        break;
      }
    }
    keep_going = i < MAX_TASKS;
  } while (keep_going);
}

void
scheduler_finalize() {
  for (uint32_t i = 0; i < MAX_TASKS; ++i) {
    fiber_free(workers[i]);
  }

  fiber_finalize();
}

void
scheduler_spawn(fiber_entry_point_t func, void *arg) {
  for (uint32_t id = 0; id < MAX_TASKS; ++id) {
      if (!fiber_allocated[id]) {
          workers[id] = fiber_alloc(func);
          fiber_ready[id] = true;
          fiber_allocated[id] = true;
          fiber_arg[id] = arg;
          return;
      }
  }
  abort(); // No available fiber slots.
}

export("render_main")
int
render_main(int time) {
    int result = -1;
    time = time+0;
    scheduler_init();
    // result = render(time);
    scheduler_spawn((fiber_entry_point_t)render_stub, (void *)(intptr_t)time);
    scheduler_loop();
    scheduler_finalize();

    return result;
}
