
import csv
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

CSV_FILE = "wasmtime_instrumented_results.csv"

# Academic-style plotting defaults
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Load and group data
data = defaultdict(list)

with open(CSV_FILE, newline="") as f:
    for row in csv.DictReader(f):
        data[(row["benchmark"], row["mode"])].append(
            float(row["ns"])
        )

# Calculate statistics
keys = sorted(data.keys())
labels = [
    f"{benchmark.removeprefix('wasi_clock_').replace('_', ' ')}"
    for benchmark, mode in keys
]

medians = np.array([
    np.median(data[k]) for k in keys
])

mins = np.array([
    np.min(data[k]) for k in keys
])

maxs = np.array([
    np.max(data[k]) for k in keys
])

# Range relative to median
errors = np.array([
    medians - mins,
    maxs - medians
])


# Assign a consistent colour to each mode
modes = sorted(set(mode for _, mode in keys))

palette = plt.cm.Set2(np.linspace(0, 1, len(modes)))
mode_colors = dict(zip(modes, palette))


# Convert nanoseconds to seconds
medians_s = medians / 1e9
mins_s = mins / 1e9
maxs_s = maxs / 1e9

errors_s = np.array([
    medians_s - mins_s,
    maxs_s - medians_s
])

# Benchmark and mode grouping
benchmarks = [
    "wasi_clock_treesum",
    "wasi_clock_pi",
    "wasi_clock_itersum",
    "wasi_clock_c10m",
]
modes = [
    "wasmfx",
    "asyncify",
]

# Muted academic colour palette
colors = {
    "asyncify": "#D28B45",
    "wasmfx": "#398F85",
}

# Fallback colours for additional modes
fallback = plt.cm.Set2(np.linspace(0, 1, len(modes)))
for mode, color in zip(modes, fallback):
    colors.setdefault(mode, color)

# Plot style
fig, ax = plt.subplots(figsize=(3.3, 2.8))

group_width = 0.3
offsets = np.linspace(
    -group_width / 2,
    group_width / 2,
    len(modes)
) if len(modes) > 1 else [0]

offsets_by_mode = dict(zip(modes, offsets))

# Plot each mode side by side for each benchmark
for mode, offset in zip(modes, offsets):
    positions = []
    values = []
    ranges = []

    for i, benchmark in enumerate(benchmarks):
        key = (benchmark, mode)

        if key not in data:
            continue

        idx = keys.index(key)

        positions.append(i + offset)
        values.append(medians_s[idx])
        ranges.append(errors_s[:, idx])

    if not positions:
        continue

    ranges = np.array(ranges).T

    ax.errorbar(
        positions,
        values,
        yerr=ranges,
        fmt="o",
        color=colors[mode],
        markerfacecolor=colors[mode],
        markeredgecolor="white",
        markeredgewidth=0.6,
        markersize=3,
        ecolor=colors[mode],
        elinewidth=1.1,
        capsize=2.5,
        label=mode,
        zorder=3,
    )

# Connect measurements and annotate relative differences
for i, benchmark in enumerate(benchmarks):

    if ("asyncify" not in modes or "wasmfx" not in modes):
        continue

    key_a = (benchmark, "asyncify")
    key_w = (benchmark, "wasmfx")

    if key_a not in keys or key_w not in keys:
        continue

    idx_a = keys.index(key_a)
    idx_w = keys.index(key_w)

    x_a = i + offsets_by_mode["asyncify"]
    x_w = i + offsets_by_mode["wasmfx"]

    y_a = medians_s[idx_a]
    y_w = medians_s[idx_w]

    # Percentage difference relative to wasmfx
    pct = (y_a - y_w) / y_w * 100

    # Dotted connector
    ax.plot(
        [x_a, x_w],
        [y_a, y_w],
        linestyle=":",
        color="#777777",
        linewidth=1,
        alpha=0.8,
        zorder=1,
    )

    # Percentage annotation
    mid_x = (x_a + x_w) / 2
    mid_y = (y_a + y_w) / 2

    # Move label away from the connecting line
    vertical_offset = 40
    horizontal_offset = 5

    ax.annotate(
        f"{pct:+.1f}%",
        (mid_x, mid_y),
        xytext=(horizontal_offset, vertical_offset),
        textcoords="offset points",
        ha="center",
        va="bottom" if pct >= 0 else "top",
        fontsize=8,
        color="#444444",
        bbox=dict(
            facecolor="white",
            edgecolor="none",
            alpha=0.85,
            pad=2
        ),
        zorder=5,
    )

# X-axis labels: benchmark names only
labels = [
    b.removeprefix("wasi_clock_").replace("_", " ")
    for b in benchmarks
]

ax.set_xticks(range(len(benchmarks)))
ax.set_xticklabels(labels)

ax.set_ylabel("Execution time (s)", labelpad=7)

# Minimal grid and axes
ax.grid(
    axis="y",
    linestyle=":",
    linewidth=0.7,
    color="#cccccc",
    alpha=0.7,
    zorder=0,
)

ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#777777")
ax.spines["bottom"].set_color("#777777")

ax.tick_params(
    axis="both",
    direction="out",
    length=3,
    width=0.7,
    colors="#333333",
)

# Legend above the plot
ax.legend(
    title=None,
    frameon=False,
    loc="lower center",
    bbox_to_anchor=(0.5, 1.02),
    ncol=len(modes),
    fontsize=8,
    handletextpad=0.4,
    columnspacing=1.5,
)

ax.set_xlim(-0.35, len(benchmarks) - 0.65)

ax.set_title("Instrumented Wasmtime Benchmarks", pad=30)

fig.tight_layout(pad=0.8)

# Export
fig.savefig("wasmtime_instrumented_results.png", dpi=300, bbox_inches="tight")

plt.show()
