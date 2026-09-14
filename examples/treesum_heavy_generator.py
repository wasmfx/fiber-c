#!/usr/bin/python3

import sys

if len(sys.argv) != 2:
    print("Usage: treesum_heavy_generator.py <extra-arg-count>")
    exit(1)

n = int(sys.argv[1])

with open(f"treesum_heavy_args.h", "w") as f:
    for i in range(n):
        print(f",    int arg{i}", file=f)

with open(f"treesum_heavy_leftcalls.h", "w") as f:
    print(f",    arg{n-1}", file=f)
    for i in range(n-1):
        print(f",    arg{i}", file=f)

with open(f"treesum_heavy_rightcalls.h", "w") as f:
    print(f",    arg{n-2}", file=f)
    print(f",    arg{n-1}", file=f)
    for i in range(n-2):
        print(f",    arg{i}", file=f)

with open(f"treesum_heavy_startcalls.h", "w") as f:
    for i in range(n):
        print(f",    i + {i}", file=f)
