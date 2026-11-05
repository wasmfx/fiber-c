#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np

file_base = "depth_results_heavy"
data = np.recfromcsv(f"{file_base}.csv")

asyncify_data = data[data["parameter_mode"] == b"asyncify"][
    ["median", "stddev", "parameter_height"]
]
wasmfx_data = data[data["parameter_mode"] == b"wasmfx"][
    ["median", "stddev", "parameter_height"]
]

plt.plot(
    asyncify_data["parameter_height"],
    asyncify_data["median"],
    label="asyncify",
    marker="o",
    color="green",
)
plt.errorbar(
    asyncify_data["parameter_height"],
    asyncify_data["median"],
    yerr=asyncify_data["stddev"],
    fmt="",
    capsize=5,
    color="green",
)

plt.plot(
    wasmfx_data["parameter_height"],
    wasmfx_data["median"],
    label="wasmfx",
    marker="s",
    color="orange",
)
plt.errorbar(
    wasmfx_data["parameter_height"],
    wasmfx_data["median"],
    yerr=wasmfx_data["stddev"],
    fmt="",
    capsize=5,
    color="orange",
)

plt.legend(["asyncify", "wasmfx"], loc="upper right")

plt.savefig(f"{file_base}.png")
plt.savefig(f"{file_base}.pdf", format="pdf")
