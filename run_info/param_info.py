#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///

"""This script dumps the parameters each benchmark was run with."""

import yaml
import subprocess
import os
import json

# We get the treesum and itersum params from the config file.
config = yaml.safe_load(open("config.yml"))

# We sed the pi and scheduler params

# sed commands to get number of fibers arguments for pi and scheduler benchmarks
pi_tasks_cmd = """awk '/#define NUM_TASKS/ { sub(".* ", ""); print }' examples/pi.c"""
scheduler_workers_cmd = """awk '/#define NUM_WORKERS/ { sub(".* ", ""); print }' examples/scheduler.c"""

# now run those commands
pi_tasks_param = subprocess.check_output(pi_tasks_cmd, shell=True, text=True).strip()
scheduler_workers_param = subprocess.check_output(scheduler_workers_cmd, shell=True, text=True).strip()

# Then sed the number of context switches
pi_yields_cmd = """awk '/YIELDS =/ { sub(".* ", ""); gsub(/;/, ""); print }' examples/pi.c"""
scheduler_switches_cmd = """awk '/#define SWITCHES/ { sub(".* ", ""); print }' examples/scheduler.c"""

# run the commands
pi_yields_param = subprocess.check_output(pi_yields_cmd, shell=True, text=True).strip()
scheduler_switches_param = subprocess.check_output(scheduler_switches_cmd, shell=True, text=True).strip()

# make the output directory if necessary
os.makedirs(f"out", exist_ok=True)

with open("out/param_info.json", "w") as f:
    json.dump({
        "treesum": str(config["BENCHMARK_ARGS"]["treesum"]),
        "itersum": str(config["BENCHMARK_ARGS"]["itersum"]),
        "pi": 
            ("tasks= " + pi_tasks_param + ", yields= " + pi_yields_param),
        "scheduler": 
            ("workers= " + scheduler_workers_param + ", switches= " + scheduler_switches_param),
        "c10m" : "N/A",
    }, f)