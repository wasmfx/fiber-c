#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///

"""This script finds out the version and flags of compiler tools used for 
    a particular benchmarking run."""

import subprocess
import json
import os

# Run makefile which dumps the compiler info
data = subprocess.check_output(["make", "-f", "run_info/compiler_info.mk"], text=True)

# Process this info into a dict
config = {}

for line in data.splitlines():
    line = line.strip()
    key, value = line.split("=", 1)
    config[key.strip()] = value.strip()

# Get version numbers of things
wasm_opt_ver = subprocess.check_output([config["wasm_opt"], "--version"]).decode().split('\n', 1)[0]
wasm_merge_ver = subprocess.check_output([config["wasm_merge"], "--version"]).decode().split('\n', 1)[0]
wasicc_ver = subprocess.check_output([config["wasicc"], "-v"], stderr=subprocess.STDOUT).decode().split('\n', 1)[0]
wasm_interp_ver = "TODO: figure out how to get version" #subprocess.check_output([config["wasm_interp"],"-v", "-e", "\"\""]).decode().split('\n', 1)[0]
wasmfxtime_ver = subprocess.check_output([config["wasmfxtime"], "--version"]).decode().split('\n', 1)[0]
# and this is wasmtime
wasmtime_ver = subprocess.check_output([config["wasmtime"], "--version"]).decode().split('\n', 1)[0]

# -------- Cleaning up the json --------

# Here's a function that strips a string of a substring between brackets
def strip_brackets(s):
    start = s.find("(")
    end = s.find(")", start)
    if start != -1 and end != -1:
        return s[:start] + s[end+1:]
    return s

# Extract version number from wasm_opt_ver (removing long number at the end)
wasm_opt_ver = strip_brackets(wasm_opt_ver)

# Extract -O flag from wasm_opt_flags
wasm_opt_flags = config["wasm_opt_flags"]
wasm_opt_flags = wasm_opt_flags[wasm_opt_flags.index("-O"):][:3]

# Extract version number from wasicc_ver (removing long url at the end)
wasicc_ver = strip_brackets(wasicc_ver)

# Extract -O flag from waiscc_flags
waiscc_flags = config["wasi_flags"]
wasicc_flags = waiscc_flags[waiscc_flags.index("-O"):][:3]

# Extract version number from wasmfxtime_ver (removing long number at the end)
wasmfxtime_ver = strip_brackets(wasmfxtime_ver)

# make the output directory if necessary
os.makedirs(f"out", exist_ok=True)

# Write this stuff to a json
with open("out/compiler_info.json", "w") as f:
    json.dump({
        "wasm_opt_ver" : wasm_opt_ver,
        "wasm_opt_flags" : wasm_opt_flags,
        "wasicc_ver" : wasicc_ver,
        "wasicc_flags" : wasicc_flags,
        "wasmfxtime_ver" : wasmfxtime_ver,
        # The commented out lines dump *all* info, which we might want at some point!
        #"wasm_opt_flags" : config["wasm_opt_flags"],
        #"asyncify_flags" : config["asyncify_flags"],
        #"wasm_merge_ver" : wasm_merge_ver,
        #"wasm_merge_flags" : config["wasm_merge_flags"],
        #"wasicc_flags" : config["wasi_flags"],
        #"wasm_interp_ver" : wasm_interp_ver,
        #"wasmtime_ver" : wasmtime_ver,
    }, f)