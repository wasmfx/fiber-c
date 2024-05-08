#ifndef WAEIO_WASM_UTILS_H
#define WAEIO_WASM_UTILS_H

#define __wasm_import__(MODULE, NAME) __attribute__((import_module(MODULE),import_name(NAME)))
#define __wasm_export__(NAME) __attribute__((export_name(NAME)))


#endif
