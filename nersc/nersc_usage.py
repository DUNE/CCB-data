#!/usr/bin/env python3
"""Summarise NERSC IRIS usage exports for the DUNE computing model.

Reads any number of IRIS "usage report" CSV exports out of a data directory and
reports totals, monthly profiles, and contiguous production blocks.  Written
against the exports for projects m3249 (production) and dune (general), but it
keys off the file contents rather than the file names, so new projects and new
allocation years drop in without code changes.

Stdlib only - no pandas - so it runs in any of the venvs around this repo.

Usage
-----
    python nersc_usage.py                       # full report over ./data
    python nersc_usage.py --data-dir /some/dir
    python nersc_usage.py --blocks m3249        # daily profile + block finding
    python nersc_usage.py --calibrate 17982 --pot 4e19

Notes
-----
IRIS reports node-hours.  A Perlmutter GPU node holds four A100s, so
literal GPU-hours = node-hours * 4.  Keep the distinction explicit; conflating
them is a silent 4x.

IRIS aggregates by user/project/host/date only.  It cannot tell you which
production *step* consumed the time.  For that you need Slurm job accounting,
e.g.

    sacct -A m3249 -S 2025-11-01 -E 2026-01-22 \
          --format=JobID,JobName%40,Partition,NNodes,Elapsed,State -X -P
"""

import argparse
import collections
import csv
import glob
import os
import sys

GPUS_PER_NODE = 4       # Perlmutter GPU node = 4x A100
POT_PER_SPILL = 7.5e13  # nominal
POT_PER_FIREWORK = 1e14  # GENIE generation unit in the ND MiniProd samples

# IRIS spells the production pseudo-user both ways across exports.
PRODUCTION_MARKERS = ("dunepro", "dunepr")


def is_production(user):
    return any(m in user for m in PRODUCTION_MARKERS)


def read_export(path):
    """Yield normalised rows from one IRIS export.

    Handles the two things that differ between exports: the leading BOM, and
    the fact that monthly reports name the date column "Month" while daily ones
    name it "Day".
    """
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            return
        datekey = "Month" if "Month" in reader.fieldnames else "Day"
        if datekey not in reader.fieldnames:
            raise ValueError(f"{path}: no Month/Day column; got {reader.fieldnames}")
        granularity = "monthly" if datekey == "Month" else "daily"
        for row in reader:
            yield {
                "date": row[datekey],
                "user": row["User"],
                "project": row["Project"],
                "host": row["Host Name"],
                "charged": _num(row.get("Node Hours Charged")),
                "raw": _num(row.get("Raw Hours")),
                "granularity": granularity,
                "source": os.path.basename(path),
            }


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# IRIS export naming has varied between pulls; match both conventions.
USAGE_GLOBS = ("nersc_*report*.csv", "*compute*.csv")
JOBS_GLOB = "jobs_*.csv"


def load(data_dir):
    """Load every usage export in data_dir, de-duplicated.

    Allocation-year exports overlap: an AY2025 pull and an AY2026 pull both
    contain 2026-01-21.  Identical rows are dropped so a day present in two
    files is not counted twice.
    """
    paths = []
    for g in USAGE_GLOBS:
        paths.extend(glob.glob(os.path.join(data_dir, g)))
    paths = sorted(set(paths))
    if not paths:
        sys.exit(f"no usage exports in {data_dir} (looked for {', '.join(USAGE_GLOBS)})")
    rows, seen, dupes = [], set(), 0
    for p in paths:
        for r in read_export(p):
            key = (r["date"], r["user"], r["project"], r["host"],
                   r["granularity"], r["charged"], r["raw"])
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            rows.append(r)
    if dupes:
        print(f"[de-duplicated {dupes} rows present in more than one export]\n")
    return rows, paths


def sel(rows, granularity=None, project=None, host=None, prod=None, lo=None, hi=None):
    out = rows
    if granularity:
        out = [r for r in out if r["granularity"] == granularity]
    if project:
        out = [r for r in out if r["project"] == project]
    if host:
        out = [r for r in out if r["host"] == host]
    if prod is not None:
        out = [r for r in out if is_production(r["user"]) == prod]
    if lo:
        out = [r for r in out if r["date"] >= lo]
    if hi:
        out = [r for r in out if r["date"] <= hi]
    return out


def total(rows, field="raw"):
    return sum(r[field] for r in rows)


# ---------------------------------------------------------------- reports


def report_coverage(rows, paths):
    print("=" * 74)
    print("COVERAGE")
    print("=" * 74)
    for p in paths:
        sub = [r for r in rows if r["source"] == os.path.basename(p)]
        dates = sorted({r["date"] for r in sub})
        print(f"  {os.path.basename(p):<46} {len(sub):>5} rows  "
              f"{dates[0]} .. {dates[-1]}")
    print("\n  NOTE: NERSC allocation years end in late January.  An export named")
    print("  '..._2025.csv' ending around 2026-01-21 is a COMPLETE allocation-year")
    print("  record, not a truncated pull.  End-of-year bursts are usually quota")
    print("  burn-down and may not correspond to a coherent production sample.")


def report_totals(rows):
    print("\n" + "=" * 74)
    print("TOTALS BY PROJECT / HOST  (raw node-hours, daily exports)")
    print("=" * 74)
    daily = sel(rows, granularity="daily")
    projects = sorted({r["project"] for r in daily})
    hosts = sorted({r["host"] for r in daily})
    print(f"  {'project':<10}{'host':<18}{'production':>14}{'users':>14}{'total':>14}")
    for proj in projects:
        for host in hosts:
            sub = sel(daily, project=proj, host=host)
            if not sub:
                continue
            p = total([r for r in sub if is_production(r["user"])])
            u = total([r for r in sub if not is_production(r["user"])])
            if p + u < 0.05:
                continue
            print(f"  {proj:<10}{host:<18}{p:>14,.0f}{u:>14,.0f}{p+u:>14,.0f}")


def report_monthly_gpu(rows):
    print("\n" + "=" * 74)
    print("PERLMUTTER GPU BY MONTH  (raw node-hours)")
    print("=" * 74)
    monthly = sel(rows, granularity="monthly", host="perlmutter gpu")
    if not monthly:
        print("  (no monthly exports loaded)")
        return
    projects = sorted({r["project"] for r in monthly})
    months = sorted({r["date"] for r in monthly})
    head = "".join(f"{p:>13}" for p in projects)
    print(f"  {'month':<12}{head}{'combined':>13}")
    totals = collections.defaultdict(float)
    split_months = set()
    for m in months:
        line, combined = "", 0.0
        for p in projects:
            cells = sel(monthly, project=p, lo=m, hi=m)
            if len({c["source"] for c in cells}) > 1:
                split_months.add(m)
            v = total(cells)
            line += f"{v:>13,.0f}"
            combined += v
            totals[p] += v
        flag = " *" if m in split_months else ""
        print(f"  {m:<12}{line}{combined:>13,.0f}{flag}")
    line = "".join(f"{totals[p]:>13,.0f}" for p in projects)
    print(f"  {'TOTAL':<12}{line}{sum(totals.values()):>13,.0f}")
    if split_months:
        print("\n  * This month is covered by more than one export (an allocation-year")
        print("    boundary falls inside it).  Each export reports its own partial")
        print("    month, so the total is nearly right but DOUBLE-COUNTS the shared")
        print("    boundary day.  Use the daily figures for these months - those are")
        print("    de-duplicated exactly.")


def report_prod_vs_analysis(rows):
    print("\n" + "=" * 74)
    print("PRODUCTION vs ANALYSIS GPU")
    print("=" * 74)
    daily = sel(rows, granularity="daily", host="perlmutter gpu")
    p = total([r for r in daily if is_production(r["user"])])
    u = total([r for r in daily if not is_production(r["user"])])
    print(f"  production (dunepro/dunepr) {p:>12,.0f} node-hr")
    print(f"  analysis / individual users {u:>12,.0f} node-hr")
    if p:
        print(f"  analysis : production       {u/p:>12,.2f}")
    print("\n  The model computes NO Analysis-GPU at all (the driver's analysis")
    print("  block loops over ['CPU'] only), so this entire category is missing.")


def find_blocks(series, threshold, gap):
    """Group active days into blocks.  series: {date: value}, sorted by date."""
    days = sorted(series)
    active = [d for d in days if series[d] >= threshold]
    if not active:
        return []
    idx = {d: i for i, d in enumerate(days)}
    blocks, cur = [], [active[0]]
    for prev, d in zip(active, active[1:]):
        if idx[d] - idx[prev] - 1 <= gap:
            cur.append(d)
        else:
            blocks.append(cur)
            cur = [d]
    blocks.append(cur)
    out = []
    for b in blocks:
        lo, hi = b[0], b[-1]
        span = [d for d in days if lo <= d <= hi]
        out.append({
            "start": lo, "end": hi,
            "total": sum(series[d] for d in span),
            "peak": max(series[d] for d in span),
            "active_days": len(b), "span_days": len(span),
        })
    return out


def report_blocks(rows, project, threshold, gap, since):
    print("\n" + "=" * 74)
    print(f"DAILY GPU PROFILE AND BLOCKS  —  {project}, production users")
    print("=" * 74)
    daily = sel(rows, granularity="daily", project=project,
                host="perlmutter gpu", prod=True, lo=since)
    cpu = sel(rows, granularity="daily", project=project,
              host="perlmutter cpu", prod=True, lo=since)
    if not daily:
        print(f"  no daily GPU rows for project {project}")
        return
    g, c = collections.defaultdict(float), collections.defaultdict(float)
    for r in daily:
        g[r["date"]] += r["raw"]
    for r in cpu:
        c[r["date"]] += r["raw"]
    scale = max(g.values()) / 44 if g else 1
    print(f"  {'date':<12}{'GPU':>10}{'CPU':>9}")
    for d in sorted(set(g) | set(c)):
        gv, cv = g.get(d, 0.0), c.get(d, 0.0)
        if gv > 0.5 or cv > 0.5:
            print(f"  {d:<12}{gv:>10,.1f}{cv:>9,.1f}  {'#' * int(gv / scale) if scale else ''}")
    blocks = find_blocks(g, threshold, gap)
    print(f"\n  blocks (threshold {threshold} node-hr/day, merge gaps <= {gap} days):")
    print(f"  {'#':<3}{'start':<12}{'end':<12}{'node-hr':>11}{'peak/day':>11}{'days':>7}")
    for i, b in enumerate(blocks, 1):
        print(f"  {i:<3}{b['start']:<12}{b['end']:<12}{b['total']:>11,.0f}"
              f"{b['peak']:>11,.0f}{b['span_days']:>7}")
    if len(blocks) > 1:
        print("\n  A GPU-heavy block with negligible CPU is reconstruction, not")
        print("  generation.  Matching blocks to named productions needs Slurm job")
        print("  names (sacct) - IRIS cannot resolve workflow steps.")


def report_jobs(data_dir):
    """Summarise IRIS job-level exports, which carry Slurm job names."""
    paths = sorted(glob.glob(os.path.join(data_dir, JOBS_GLOB)))
    if not paths:
        return
    print("\n" + "=" * 74)
    print("JOB-LEVEL EXPORTS  (job names reveal the workflow step)")
    print("=" * 74)
    for p in paths:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            jobs = list(csv.DictReader(fh))
        if not jobs:
            continue
        starts = sorted(j["Start"] for j in jobs if j.get("Start"))
        accts = sorted({j.get("Account Name", "") for j in jobs})
        print(f"\n  {os.path.basename(p)}  —  {len(jobs)} jobs")
        print(f"    {starts[0]} .. {starts[-1]}   accounts: {accts}")
        agg = collections.defaultdict(lambda: [0, 0.0])
        for j in jobs:
            agg[j.get("Job Name", "?")][0] += 1
            agg[j.get("Job Name", "?")][1] += _num(j.get("Raw Hours"))
        for name, (n, h) in sorted(agg.items(), key=lambda kv: -kv[1][1]):
            print(f"      {name[:46]:<48}{n:>5} jobs {h:>10,.1f} node-hr")
    print("\n  'fw_' = fireworks.  A GPU/CPU split in the job names is the")
    print("  mapping from node-hours to workflow step that IRIS usage reports")
    print("  cannot give you.  These exports cover the 'dune' project only;")
    print("  production (m3249) job names need sacct.")


def report_calibration(node_hours, pot, label):
    print("\n" + "=" * 74)
    print("CALIBRATION")
    print("=" * 74)
    spills = pot / POT_PER_SPILL
    pot_e18 = pot / 1e18
    print(f"  input           : {node_hours:,.0f} GPU node-hours ({label})")
    print(f"  POT             : {pot:.4g}  = {spills:,.0f} spills at {POT_PER_SPILL:.2g} POT/spill")
    print(f"                              = {pot / POT_PER_FIREWORK:,.0f} fireworks at {POT_PER_FIREWORK:.0e} POT/firework")
    print(f"  1 firework      = {POT_PER_FIREWORK / POT_PER_SPILL:.3f} spills")
    print()
    print(f"  rate            : {node_hours / pot_e18:,.1f} GPU node-hr per 1e18 POT")
    print(f"                  : {node_hours / spills:.6f} node-hr per spill")
    print(f"                  : {node_hours * GPUS_PER_NODE / spills:.5f} GPU-hr per spill"
          f"   <- model 'Reco-*-GPU' if an ND event means a spill")
    print(f"                  : {node_hours * GPUS_PER_NODE / spills * 3600:,.0f} GPU-sec per spill")
    print()
    print("  For reference, the values currently in the JSON:")
    print("    ND-LAr+TMS Reco-Data-GPU = 0.76     (2023 estimate, un-renormalised)")
    print("    ND-LAr+TMS Reco-Sim-GPU  = 0.0222   (benchmark-derived, not from these logs)")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=os.path.join(here, "data"))
    ap.add_argument("--blocks", metavar="PROJECT",
                    help="daily profile + block finding for this project")
    ap.add_argument("--threshold", type=float, default=50.0,
                    help="node-hr/day for a day to count as active (default 50)")
    ap.add_argument("--gap", type=int, default=3,
                    help="inactive days bridged within a block (default 3)")
    ap.add_argument("--since", default="2025-10-01",
                    help="earliest date for the daily profile (default 2025-10-01)")
    ap.add_argument("--calibrate", type=float, metavar="NODE_HOURS",
                    help="GPU node-hours to turn into a per-spill rate")
    ap.add_argument("--pot", type=float, default=4e19,
                    help="POT the --calibrate sample covers (default 4e19)")
    ap.add_argument("--label", default="user-supplied")
    args = ap.parse_args()

    rows, paths = load(args.data_dir)
    report_coverage(rows, paths)
    report_totals(rows)
    report_monthly_gpu(rows)
    report_prod_vs_analysis(rows)
    report_jobs(args.data_dir)
    if args.blocks:
        report_blocks(rows, args.blocks, args.threshold, args.gap, args.since)
    if args.calibrate:
        report_calibration(args.calibrate, args.pot, args.label)


if __name__ == "__main__":
    main()
