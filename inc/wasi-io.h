#ifndef __WASI_IO_H
#define __WASI_IO_H

#include <stdint.h>
#include <unistd.h>
#include <wasi/api.h>

// NOTE: We cannot use printf() and most friends because asyncify
// attempts to transform them and inadvertently ending up corrupting
// its own state resulting in an "unreachable" error at runtime.
// The following code is adapted from
//   https://gist.github.com/s-macke/6dd78c78be46214d418454abb667a1ba
#define wasi_print(str) do { \
    const uint8_t *start = (uint8_t *)str; \
    const uint8_t *end = start; \
    for (; *end != '\0'; end++) {} \
    __wasi_ciovec_t iov = {.buf = start, .buf_len = end - start}; \
    size_t nwritten; \
    (void)__wasi_fd_write(STDOUT_FILENO, &iov, 1, &nwritten);   \
} while (0)
#define wasi_print_debug(str) \
    wasi_print(__FILE__ ":" STRINGIZE(__LINE__) ": " str "\n")
#define wasi_printc(ch) do { \
    const char str[] = { ch }; \
    wasi_print(str); \
} while (0)
#endif
