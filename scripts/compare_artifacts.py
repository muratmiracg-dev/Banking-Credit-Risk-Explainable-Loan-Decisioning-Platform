#!/usr/bin/env python3
"""Compare regenerated analytics evidence with a committed snapshot.

The pipeline is deterministic, but its numbers depend on library versions
(for example scikit-learn 1.9 changes HistGradientBoosting results). CI copies
the committed artifacts aside, reruns the pipeline and calls this script so a
dependency drift that silently changes published metrics fails the build.

CSV (optionally gzip-compressed) and JSON files are compared value by value:
text must match exactly, numbers within a relative/absolute tolerance that
absorbs platform floating-point noise. Binary files (plots, pickles) are not
byte-comparable across platforms and are skipped; their content is covered by
the numeric outputs they are derived from.

Usage: compare_artifacts.py COMMITTED_DIR REGENERATED_DIR
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REL_TOL = 1e-9
ABS_TOL = 1e-12
TEXT_SUFFIXES = (".csv", ".csv.gz", ".json")


def _is_compared(path: Path) -> bool:
    return path.name.endswith(TEXT_SUFFIXES)


def _close(left: float, right: float) -> bool:
    if math.isnan(left) and math.isnan(right):
        return True
    return math.isclose(left, right, rel_tol=REL_TOL, abs_tol=ABS_TOL)


def compare_json(left: object, right: object, where: str = "$") -> list[str]:
    if isinstance(left, bool) or isinstance(right, bool):
        return [] if left == right else [f"{where}: {left!r} != {right!r}"]
    if isinstance(left, int | float) and isinstance(right, int | float):
        return [] if _close(float(left), float(right)) else [f"{where}: {left!r} != {right!r}"]
    if isinstance(left, dict) and isinstance(right, dict):
        problems = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                problems.append(f"{where}.{key}: present on one side only")
            else:
                problems.extend(compare_json(left[key], right[key], f"{where}.{key}"))
        return problems
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return [f"{where}: length {len(left)} != {len(right)}"]
        problems = []
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            problems.extend(compare_json(a, b, f"{where}[{index}]"))
        return problems
    return [] if left == right else [f"{where}: {left!r} != {right!r}"]


def compare_csv(left: Path, right: Path) -> list[str]:
    a = pd.read_csv(left, keep_default_na=False)
    b = pd.read_csv(right, keep_default_na=False)
    if list(a.columns) != list(b.columns):
        return [f"columns differ: {list(a.columns)} != {list(b.columns)}"]
    if len(a) != len(b):
        return [f"row count {len(a)} != {len(b)}"]
    problems = []
    for column in a.columns:
        x, y = a[column], b[column]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            xv, yv = x.to_numpy(dtype=float), y.to_numpy(dtype=float)
            ok = np.isclose(xv, yv, rtol=REL_TOL, atol=ABS_TOL, equal_nan=True)
        else:
            ok = (x.astype(str) == y.astype(str)).to_numpy()
        if not ok.all():
            row = int(np.flatnonzero(~ok)[0])
            problems.append(
                f"column {column!r}: {int((~ok).sum())} value(s) differ, "
                f"first at row {row}: {x.iloc[row]!r} != {y.iloc[row]!r}"
            )
    return problems


def compare_trees(committed: Path, regenerated: Path) -> list[str]:
    problems: list[str] = []
    files = sorted(p for p in committed.rglob("*") if p.is_file() and _is_compared(p))
    if not files:
        return [f"no comparable files under {committed}"]
    for old in files:
        relative = old.relative_to(committed)
        new = regenerated / relative
        if not new.is_file():
            problems.append(f"{relative}: missing after regeneration")
            continue
        if old.name.endswith(".json"):
            diffs = compare_json(
                json.loads(old.read_text(encoding="utf-8")),
                json.loads(new.read_text(encoding="utf-8")),
            )
        else:
            diffs = compare_csv(old, new)
        problems.extend(f"{relative}: {diff}" for diff in diffs[:5])
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("committed", type=Path)
    parser.add_argument("regenerated", type=Path)
    args = parser.parse_args(argv)
    problems = compare_trees(args.committed, args.regenerated)
    if problems:
        print("Regenerated artifacts drifted from the committed evidence:")
        print(*(f"- {p}" for p in problems), sep="\n")
        print("Pin the dependency that changed or rerun the pipeline and commit the outputs.")
        return 1
    print(f"Regenerated artifacts match committed evidence ({REL_TOL=}, {ABS_TOL=}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
