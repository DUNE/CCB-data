#!/usr/bin/env python3
"""Analyse Slurm job accounting (sacct) exports for DUNE NERSC production.

IRIS usage reports say how many node-hours were spent; they cannot say on
*what*. Slurm job accounting carries job names, which for this workflow do
identify the stage. This script turns a sacct dump into a breakdown by
workflow stage and month, and cross-checks the node-hours against IRIS.

Produce the input with nersc/sacct_pull.sh (see nersc/README.md). Files may
be plain text or gzipped.

Usage
-----
    python sacct_jobs.py                        # full report over ./data
    python sacct_jobs.py --project m3249
    python sacct_jobs.py --names --project m3249    # raw job-name listing
    python sacct_jobs.py --window 2025-11-01 2026-02-28

Node-hours are NNodes x Elapsed. That is exact for exclusive-node
partitions, which is what production uses. It OVERSTATES usage on the
`shared_*` partitions, where a job books one node but is charged a
fraction; those matter for the general `dune` project, not for m3249.
"""

import argparse
import collections
import csv
import glob
import gzip
import io
import os
import re
import sys

GPUS_PER_NODE = 4
POT_PER_SPILL = 7.5e13

# Workflow stages, in report order. First match wins.
STAGES = [
    ("fireworks production", lambda n: n.startswith("fw_")),
    ("Spine ML training",    lambda n: re.match(r"^(Spn|SpTr)", n) is not None),
    ("larnd-sim / seg",      lambda n: "larnd" in n or n.startswith("SegFFE")),
    ("MiniProd (named)",     lambda n: "MiniProd" in n),
    ("rock generation",      lambda n: n.startswith("GenRock")),
    ("interactive / misc",   lambda n: n == "interactive" or n.startswith("bl_")),
]


def stage(name):
    for label, test in STAGES:
        if test(name):
            return label
    return "other"


def parse_elapsed(s):
    """sacct Elapsed, [DD-]HH:MM:SS, as hours."""
    s = (s or "").strip()
    if not s:
        return 0.0
    days = 0
    if "-" in s:
        d, s = s.split("-", 1)
        try:
            days = int(d)
        except ValueError:
            return 0.0
    parts = s.split(":")
    try:
        nums = [int(x) for x in parts]
    except ValueError:
        return 0.0
    while len(nums) < 3:
        nums.insert(0, 0)
    h, m, sec = nums[-3:]
    return days * 24 + h + m / 60 + sec / 3600


def _open(path):
    if path.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", newline="")
    return open(path, encoding="utf-8", newline="")


def load(path):
    rows = []
    with _open(path) as fh:
        for r in csv.DictReader(fh, delimiter="|"):
            if not r.get("JobID"):
                continue
            try:
                nn = int(r.get("NNodes") or 0)
            except ValueError:
                nn = 0
            el = parse_elapsed(r.get("Elapsed"))
            start = (r.get("Start") or "").strip()
            rows.append({
                "name": (r.get("JobName") or "").strip(),
                "acct": (r.get("Account") or "").strip(),
                "user": (r.get("User") or "").strip(),
                "part": (r.get("Partition") or "").strip(),
                "state": (r.get("State") or "").strip(),
                "start": start,
                "month": start[:7] if start[:1].isdigit() else None,
                "day": start[:10] if start[:1].isdigit() else None,
                "nodehours": nn * el,
                "gpu": (r.get("Account") or "").strip().endswith("_g")
                       or "gpu" in (r.get("Partition") or "").lower(),
            })
    return rows


def load_all(data_dir, project=None):
    pat = f"sacct_{project}.txt*" if project else "sacct_*.txt*"
    paths = sorted(glob.glob(os.path.join(data_dir, pat)))
    if not paths:
        sys.exit(f"no sacct exports matching {pat} in {data_dir}")
    out = {}
    for p in paths:
        name = os.path.basename(p).replace("sacct_", "").split(".")[0]
        out[name] = load(p)
    return out


def report_overview(name, rows):
    print("=" * 78)
    print(f"sacct_{name}  —  {len(rows):,} jobs")
    print("=" * 78)
    starts = sorted(r["start"] for r in rows if r["day"])
    if starts:
        print(f"  start range : {starts[0]}  ..  {starts[-1]}")
        print("  NOTE: Slurm accounting retention is finite. A range starting later")
        print("  than you asked for means the earlier records have aged out.")
    states = collections.Counter(r["state"].split()[0] for r in rows)
    print(f"  states      : {dict(states.most_common(6))}")
    for lbl, want in (("GPU", True), ("CPU", False)):
        sub = [r for r in rows if r["gpu"] == want]
        print(f"  {lbl} jobs    : {len(sub):>7,}   {sum(r['nodehours'] for r in sub):>11,.0f} node-hours")
    shared = sum(r["nodehours"] for r in rows if "shared" in r["part"])
    if shared > 0.01 * sum(r["nodehours"] for r in rows):
        print(f"  WARNING: {shared:,.0f} node-hours are on shared_* partitions, where")
        print("  NNodes x Elapsed overstates real usage. Treat those as upper bounds.")


def report_stages(rows, resource="gpu"):
    want = resource == "gpu"
    sub = [r for r in rows if r["gpu"] == want and r["month"]]
    if not sub:
        return
    by = collections.defaultdict(lambda: collections.defaultdict(float))
    for r in sub:
        by[r["month"]][stage(r["name"])] += r["nodehours"]
    stages = [s for s, _ in STAGES] + ["other"]
    stages = [s for s in stages if any(by[m].get(s) for m in by)]
    print(f"\n  {resource.upper()} node-hours by month and workflow stage")
    print("  " + "month".ljust(10) + "".join(f"{s[:14]:>16}" for s in stages))
    tot = collections.defaultdict(float)
    for m in sorted(by):
        line = ""
        for s in stages:
            v = by[m].get(s, 0.0)
            tot[s] += v
            line += f"{v:>16,.0f}"
        print("  " + m.ljust(10) + line)
    print("  " + "-" * (10 + 16 * len(stages)))
    print("  " + "TOTAL".ljust(10) + "".join(f"{tot[s]:>16,.0f}" for s in stages))
    grand = sum(tot.values())
    if grand:
        print("  " + "share".ljust(10) + "".join(f"{100*tot[s]/grand:>15.1f}%" for s in stages))


def report_names(rows, limit=20):
    print("\n  job names by node-hours")
    for lbl, want in (("GPU", True), ("CPU", False)):
        sub = [r for r in rows if r["gpu"] == want]
        agg = collections.defaultdict(lambda: [0, 0.0, "", ""])
        for r in sub:
            a = agg[r["name"]]
            a[0] += 1
            a[1] += r["nodehours"]
            if r["day"]:
                a[2] = min(a[2] or r["day"], r["day"])
                a[3] = max(a[3], r["day"])
        print(f"\n    --- {lbl} ({len(agg):,} distinct names) ---")
        print(f"    {'job name':<36}{'jobs':>8}{'node-hr':>12}  {'first':<12}{'last':<12}")
        for n, (c, h, f, l) in sorted(agg.items(), key=lambda kv: -kv[1][1])[:limit]:
            print(f"    {n[:34]:<36}{c:>8,}{h:>12,.0f}  {f:<12}{l:<12}")


def report_window(rows, lo, hi):
    sub = [r for r in rows if r["day"] and lo <= r["day"] <= hi]
    print(f"\n  WINDOW {lo} .. {hi}")
    by = collections.defaultdict(lambda: [0.0, 0.0])
    for r in sub:
        by[stage(r["name"])][0 if r["gpu"] else 1] += r["nodehours"]
    print(f"    {'stage':<26}{'GPU':>12}{'CPU':>12}")
    for s, (g, c) in sorted(by.items(), key=lambda kv: -kv[1][0]):
        print(f"    {s:<26}{g:>12,.0f}{c:>12,.0f}")
    prod = by.get("fireworks production", [0.0, 0.0])[0]
    if prod:
        print(f"\n    production GPU in window: {prod:,.0f} node-hours")
        print(f"    {'POT assumption':<40}{'nh/1e18':>10}{'GPU-hr/spill':>14}")
        for lbl, pot_e18 in (("2e19", 20), ("2.77e19", 27.7), ("4e19", 40)):
            rate = prod / pot_e18
            print(f"    {lbl:<40}{rate:>10,.0f}"
                  f"{rate * GPUS_PER_NODE / (1e18 / POT_PER_SPILL):>14.3f}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=os.path.join(here, "data"))
    ap.add_argument("--project", help="limit to one project, e.g. m3249")
    ap.add_argument("--names", action="store_true", help="list job names")
    ap.add_argument("--window", nargs=2, metavar=("FROM", "TO"),
                    help="stage breakdown and calibration for a date window")
    args = ap.parse_args()

    for name, rows in load_all(args.data_dir, args.project).items():
        report_overview(name, rows)
        report_stages(rows, "gpu")
        report_stages(rows, "cpu")
        if args.names:
            report_names(rows)
        if args.window:
            report_window(rows, *args.window)
        print()


if __name__ == "__main__":
    main()
