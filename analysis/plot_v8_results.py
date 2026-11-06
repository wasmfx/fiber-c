import csv
import numpy as np
import matplotlib.pyplot as plt
import sys
from collections import defaultdict

# Input CSV (default: results.csv)
csv_file = sys.argv[1] if len(sys.argv) > 1 else "results.csv"

# Store measurements by benchmark/mode combination
results = defaultdict(list)

with open(csv_file, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        benchmark = row["benchmark"]
        mode = row["mode"]
        ns = float(row["ns"])

        results[(benchmark, mode)].append(ns)

# Calculate medians
labels = []
medians = []

for (benchmark, mode), measurements in results.items():
    labels.append(f"{benchmark}\n{mode}")
    medians.append(np.median(measurements))


# Convert nanoseconds to seconds
medians_sec = np.array(medians) / 1e9

# Create bar chart
plt.figure(figsize=(12, 6))

bars = plt.bar(labels, medians_sec, color="steelblue")

plt.xlabel("Benchmark / Mode")
plt.ylabel("Median execution time (seconds)")
plt.title("Medians from instrumented V8 runs")

plt.xticks(rotation=45, ha="right")
plt.grid(axis="y", linestyle="--", alpha=0.4)

# Add values above bars
for bar in bars:
    height = bar.get_height()

    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        f"{height:.2f}",
        ha="center",
        va="bottom",
        fontsize=8
    )

plt.tight_layout()

# Save chart
plt.savefig("v8_instrumented_results.png", dpi=300)

plt.show()

# Print summary
print("\nMedian execution times:")

for label, median in zip(labels, medians):
    print(f"{label.replace(chr(10), ' / ')}: {median:.0f} ns")
