#!/usr/bin/python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Configuration
# -----------------------------

INPUT_FILE = "data.csv"
OUTPUT_PDF = "benchmark_comparison.pdf"
OUTPUT_PNG = "benchmark_comparison.png"

# Benchmarks and their visual ordering
BENCHMARK_ORDER = ["itersum", "treesum", "pi"]

# Publication-friendly colors
COLORS = {
    "itersum": "#4477AA",
    "treesum": "#EE6677",
    "pi": "#CCBB44",
}

# -----------------------------
# Load and clean data
# -----------------------------

df = pd.read_csv(INPUT_FILE, skipinitialspace=True)

df.columns = df.columns.str.strip()
df["benchmark"] = df["benchmark"].str.strip().str.lower()
df["language"] = df["language"].str.strip().str.lower()

numeric_columns = [
    "Baseline",
    "Baseline-range",
    "Wasmfx",
    "Wasmfx-range",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove incomplete or invalid measurements
df = df.dropna(subset=["Baseline", "Wasmfx"])
df = df[(df["Baseline"] > 0) & (df["Wasmfx"] > 0)]

# -----------------------------
# Calculate ratios and errors
# -----------------------------

df["ratio"] = df["Baseline"] / df["Wasmfx"]

# Propagate measurement ranges assuming independent uncertainties.
# For R = B / W:
# sigma_R = R * sqrt((sigma_B/B)^2 + (sigma_W/W)^2)

df["ratio_error"] = df["ratio"] * np.sqrt(
    (df["Baseline-range"] / df["Baseline"]) ** 2
    + (df["Wasmfx-range"] / df["Wasmfx"]) ** 2
)

# -----------------------------
# Plot configuration
# -----------------------------

present_languages = df["language"].unique()  # to verify
languages = ["c", "go", "kotlin", "ocaml"]
assert (sorted(present_languages)== sorted(languages))

benchmarks = [
    b for b in BENCHMARK_ORDER
    if b in df["benchmark"].unique()
]

x = np.arange(len(languages))
n_benchmarks = len(benchmarks)

bar_width = 0.8 / n_benchmarks

fig, ax = plt.subplots(figsize=(8, 4.5))

# -----------------------------
# Draw grouped bars
# -----------------------------

for i, benchmark in enumerate(benchmarks):

    subset = (
        df[df["benchmark"] == benchmark]
        .set_index("language")
    )

    positions = x + (i - (n_benchmarks - 1) / 2) * bar_width

    values = [
        subset.loc[lang, "ratio"] if lang in subset.index else np.nan
        for lang in languages
    ]

    errors = [
        subset.loc[lang, "ratio_error"] if lang in subset.index else np.nan
        for lang in languages
    ]

    ax.bar(
        positions,
        values,
        width=bar_width * 0.9,
        label=benchmark,
        color=COLORS[benchmark],
        # yerr=errors,
        capsize=3,
        edgecolor="black",
        linewidth=0.6,
        error_kw={"elinewidth": 0.8},
    )

# -----------------------------
# Formatting
# -----------------------------

ax.axhline(
    y=1.0,
    color="black",
    linestyle="--",
    linewidth=1,
    alpha=0.7,
    label="Equal performance",
)

ax.set_xticks(x)
ax.set_xticklabels([lang.capitalize() for lang in languages])

ax.set_ylabel("Ratio (Baseline / Wasmfx)")

ax.legend(
    # title="Benchmark",
    frameon=False,
    ncol=2,
)

ax.grid(
    axis="y",
    linestyle=":",
    alpha=0.4,
)

ax.set_axisbelow(True)

# Remove unnecessary borders
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()

# -----------------------------
# Export publication figures
# -----------------------------

fig.savefig(
    OUTPUT_PDF,
    bbox_inches="tight",
)

fig.savefig(
    OUTPUT_PNG,
    dpi=300,
    bbox_inches="tight",
)

plt.show()

print("Calculated ratios:")
print(
    df[["benchmark", "language", "ratio", "ratio_error"]]
    .to_string(index=False)
)

print(f"\nSaved {OUTPUT_PDF} and {OUTPUT_PNG}")
