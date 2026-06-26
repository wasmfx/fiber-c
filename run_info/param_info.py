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

# We sed the pi and scheduler for number of fibers
pi_tasks_param = subprocess.check_output(["awk", '/#define NUM_TASKS/ { sub(".* ", ""); print }', "examples/pi.c"], text=True).strip()
scheduler_workers_param = subprocess.check_output(["awk", '/#define NUM_WORKERS/ { sub(".* ", ""); print }', "examples/scheduler.c"], text=True).strip()

# Then sed the number of context switches
pi_yields_param = subprocess.check_output(["awk", '/YIELDS =/ { sub(".* ", ""); gsub(/;/, ""); print }', "examples/pi.c"], text=True).strip()
scheduler_switches_param = subprocess.check_output(["awk", '/#define SWITCHES/ { sub(".* ", ""); print }', "examples/scheduler.c"], text=True).strip()

def main(arg):
    # make the output directory if necessary
    os.makedirs(str(arg), exist_ok=True)

    with open(f"{str(arg)}/param_info.json", "w") as f:
        json.dump({
            "treesum": str(config["BENCHMARK_ARGS"]["treesum"]),
            "treesum_switch": str(config["BENCHMARK_ARGS"]["treesum"]),
            "itersum": str(config["BENCHMARK_ARGS"]["itersum"]),
            "itersum_switch": str(config["BENCHMARK_ARGS"]["itersum"]),
            "pi": 
                ("tasks= " + pi_tasks_param + ", yields= " + pi_yields_param),
            "pi_switch": 
                ("tasks= " + pi_tasks_param + ", yields= " + pi_yields_param),
            "scheduler": 
                ("workers= " + scheduler_workers_param + ", switches= " + scheduler_switches_param),
            "scheduler_switch": 
                ("workers= " + scheduler_workers_param + ", switches= " + scheduler_switches_param),
            "c10m" : "N/A",
            "c10m_switch" : "N/A",
        }, f)

if __name__ == "__main__":
    import sys
    # Set default output directory to "out" if no argument is provided
    arg = sys.argv[1] if len(sys.argv) > 1 else "out"
    main(arg)