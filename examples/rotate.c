// Benchmark suspending repeatedly with a large live WebAssembly
// operand stack.
//
// Description:
//
// The `rotate` kernel has three phases:
//
// 1. It loads `ROTATE_FRAME_WORDS` values from `frame_values` onto the
// WebAssembly operand stack. With the default 8192 words, this
// creates a 32 KiB live stack frame.
//
// 2. It repeatedly calls ``fiber_yield`` while leaving those values
// untouched beneath the yield loop. Between the first yield and
// resume, `main` overwrites ``frame_values``, ensuring the engine cannot
// correctly recreate the frame by reloading memory.
//
// 3. After the final resume, it reduces the saved values with a
// right-rotation chain:
//
```text
// result = rotr(value[8191], 0)
// result = rotr(value[8190], result)
// ...
// result = rotr(value[0], result)
```
//
// The result is compared with a checksum computed from the original
// memory contents. If the suspended operand stack was lost or
// recomputed from the modified memory, the assertion fails.
//
// There is almost no computation between suspensions, so repeated
// runs primarily exercise preservation and restoration of the large
// live frame.

#include <assert.h>
#include <stdint.h>
#include <stdlib.h>

#include <fiber.h>

// Compile time parameter, valid inputs are powers of two from 0
// through 8192.
#ifndef ROTATE_FRAME_WORDS
#define ROTATE_FRAME_WORDS 8192
#endif

#define ROTATE_STORAGE_WORDS (ROTATE_FRAME_WORDS == 0 ? 1 : ROTATE_FRAME_WORDS)

static volatile uint32_t frame_values[ROTATE_STORAGE_WORDS];

#define WASM_PUSH_NEXT                                                         \
  "local.get %0\n\t"                                                           \
  "i32.load 0\n\t"                                                             \
  "local.get %0\n\t"                                                           \
  "i32.const 4\n\t"                                                            \
  "i32.add\n\t"                                                                \
  "local.set %0\n\t"

#define REPEAT_0(X)
#define REPEAT_1(X) X
#define REPEAT_2(X) REPEAT_1(X) REPEAT_1(X)
#define REPEAT_4(X) REPEAT_2(X) REPEAT_2(X)
#define REPEAT_8(X) REPEAT_4(X) REPEAT_4(X)
#define REPEAT_16(X) REPEAT_8(X) REPEAT_8(X)
#define REPEAT_32(X) REPEAT_16(X) REPEAT_16(X)
#define REPEAT_64(X) REPEAT_32(X) REPEAT_32(X)
#define REPEAT_128(X) REPEAT_64(X) REPEAT_64(X)
#define REPEAT_256(X) REPEAT_128(X) REPEAT_128(X)
#define REPEAT_512(X) REPEAT_256(X) REPEAT_256(X)
#define REPEAT_1024(X) REPEAT_512(X) REPEAT_512(X)
#define REPEAT_2048(X) REPEAT_1024(X) REPEAT_1024(X)
#define REPEAT_4096(X) REPEAT_2048(X) REPEAT_2048(X)
#define REPEAT_8192(X) REPEAT_4096(X) REPEAT_4096(X)

#define CONCAT_IMPL(A, B) A##B
#define CONCAT(A, B) CONCAT_IMPL(A, B)
#define REPEAT_N(N, X) CONCAT(REPEAT_, N)(X)
#define REPEAT_FRAME(X) REPEAT_N(ROTATE_FRAME_WORDS, X)

static_assert(ROTATE_FRAME_WORDS <= 8192,
               "ROTATE_FRAME_WORDS must not exceed 8192");
static_assert(ROTATE_FRAME_WORDS == 0 ||
                   (ROTATE_FRAME_WORDS & (ROTATE_FRAME_WORDS - 1)) == 0,
               "ROTATE_FRAME_WORDS must be zero or a power of two");

static uint32_t rotr32(uint32_t value, uint32_t amount) {
  uint32_t const shift = amount & 31;
  return (value >> shift) | (value << ((32 - shift) & 31));
}

static void fill_frame(uint32_t seed) {
  for (uint32_t i = 0; i < ROTATE_FRAME_WORDS; ++i)
    frame_values[i] = seed + i * UINT32_C(0x9e3779b9);
}

static uint32_t frame_checksum(void) {
  uint32_t result = 0;
  for (uint32_t i = ROTATE_FRAME_WORDS; i > 0; --i)
    result = rotr32(frame_values[i - 1], result);
  return result;
}

#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Woverlength-strings"
static void *rotate(void *arg) {
  uint32_t remaining = (uint32_t)(uintptr_t)arg;
  volatile uint32_t *cursor = frame_values;
  uint32_t result;

  // Load the frame once, then keep every value live below a loop that
  // yields repeatedly. The backing memory is changed after the first
  // suspension, so moving or repeating these loads after a resume
  // changes the checksum.
  __asm__ volatile(
      REPEAT_FRAME(WASM_PUSH_NEXT)
      ".functype fiber_yield (i32) -> (i32)\n\t"
      "loop\n\t"
      "i32.const 0\n\t"
      "call fiber_yield\n\t"
      "drop\n\t"
      "local.get %1\n\t"
      "i32.const 1\n\t"
      "i32.sub\n\t"
      "local.tee %1\n\t"
      "br_if 0\n\t"
      "end_loop\n\t"
      "i32.const 0\n\t"
      REPEAT_FRAME("i32.rotr\n\t")
      "local.set %2"
      : "+r"(cursor), "+r"(remaining), "=r"(result)
      :
      : "memory");

  return (void *)(uintptr_t)result;
}
#pragma clang diagnostic pop

int main(int argc, char *argv[]) {
  if (argc != 2)
    return 2;

  uint32_t const suspensions = (uint32_t)strtoul(argv[1], NULL, 10);
  if (suspensions == 0)
    return 2;

  fill_frame(UINT32_C(0x12345678));
  uint32_t const expected = frame_checksum();

  fiber_init();
  fiber_t const fiber = fiber_alloc(rotate);
  assert(fiber && "fiber allocation failed");

  fiber_result_t status;
  void *observed = fiber_resume(fiber, (void *)(uintptr_t)suspensions, &status);
  assert(status == FIBER_YIELD && "expected initial suspension");

  // Make recomputing the frame from memory observably incorrect.
  fill_frame(UINT32_C(0x87654321));
  if (ROTATE_FRAME_WORDS != 0)
    assert(frame_checksum() != expected && "test patterns must differ");

  uint32_t yielded = 0;
  while (status == FIBER_YIELD) {
    ++yielded;
    observed = fiber_resume(fiber, NULL, &status);
  }

  assert(status == FIBER_OK && "expected fiber completion");
  assert(yielded == suspensions && "unexpected suspension count");
  assert((uint32_t)(uintptr_t)observed == expected &&
         "live frame was not preserved across suspension");

  fiber_free(fiber);
  fiber_finalize();
  return 0;
}

#undef ROTATE_FRAME_WORDS
#undef ROTATE_STORAGE_WORDS
#undef WASM_PUSH_NEXT
#undef REPEAT_0
#undef REPEAT_1
#undef REPEAT_2
#undef REPEAT_4
#undef REPEAT_8
#undef REPEAT_16
#undef REPEAT_32
#undef REPEAT_64
#undef REPEAT_128
#undef REPEAT_256
#undef REPEAT_512
#undef REPEAT_1024
#undef REPEAT_2048
#undef REPEAT_4096
#undef REPEAT_8192
#undef CONCAT_IMPL
#undef CONCAT
#undef REPEAT_N
#undef REPEAT_FRAME

