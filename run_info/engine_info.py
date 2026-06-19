#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///

"""This script finds out the version and flags of each wasm engine used for 
    a particular benchmarking run."""

import yaml
import subprocess
import json
import os

config = yaml.safe_load(open("config.yml"))

# Set up environment variables for directory containing engines, defaulting to `/opt/wasmfx`` if not set
ENGINE_ROOT_DIR = os.getenv("ENGINE_ROOT_DIR", "/opt/wasmfx")

# Run --version on each engine and write the output to a file.
wasmtime_ver = subprocess.check_output([ENGINE_ROOT_DIR + config["WASMTIME_PATH"], "--version"])
wasmtime_ver = wasmtime_ver.decode().split('\n', 1)[0]

wizard_ver = subprocess.check_output([ENGINE_ROOT_DIR + config["WIZARD_PATH"], "--version"])
wizard_ver = wizard_ver.decode().split('\n', 1)[0]

v8_ver = subprocess.check_output(
    [ENGINE_ROOT_DIR + config["D8_PATH"]],
    input="quit()\n",
    text=True
)
v8_ver = v8_ver.split('\n', 1)[0]

# make the output directory if necessary
os.makedirs(f"out", exist_ok=True)

# Write this stuff to a json
with open("out/engine_info.json", "w") as f:
    json.dump({
        "wasmtime": wasmtime_ver,
        #"wasmtime_flags": config["WASMTIME_OPTIONS"],
        "wizard": wizard_ver,
        #"wizard_flags": config["WIZARD_OPTIONS"],
        "d8": v8_ver,
        #"v8_flags": config["D8_OPTIONS"],
    }, f)