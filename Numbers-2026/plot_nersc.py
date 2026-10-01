#!/usr/bin/env python3
"""Plot NERSC usage from IRIS daily/monthly report CSVs.

Focuses on perlmutter gpu but prints summaries for all host types.

Usage:
    python plot_nersc.py                  # run all 4 variants
    python plot_nersc.py monthly dune     # just monthly + project dune
    python plot_nersc.py daily m3249      # just daily + project m3249
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DATADIR = "data"

# production pseudo-users to show separately
PROD_USERS = {"Pseudo User, dunepr", "Pseudo User, dunepro"}

VARIANTS = {
    ("monthly", "dune"): "nersc_monthly_report_project_dune_2025.csv",
    ("monthly", "m3249"): "nersc_monthly_report_project_m3249_2025.csv",
    ("daily", "dune"): "nersc_daily_report_project_dune_2025.csv",
    ("daily", "m3249"): "nersc_daily_report_project_m3249_2025.csv",
}


def read_data(filename):
    """Read CSV and return list of row dicts with a normalized 'Date' key."""
    rows = []
    with open(filename, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # normalize: daily files have "Day", monthly have "Month"
            if "Day" in row:
                row["Date"] = row["Day"]
            elif "Month" in row:
                row["Date"] = row["Month"]
            rows.append(row)
    return rows


def aggregate(rows):
    """Aggregate node hours by (date, host, category).

    category is 'production' for PROD_USERS, 'other' for everyone else.
    Returns dict: (date, host, category) -> {charged, raw}
    """
    data = defaultdict(lambda: {"charged": 0.0, "raw": 0.0})
    for row in rows:
        date = row["Date"]
        host = row["Host Name"]
        user = row["User"]
        charged = float(row["Node Hours Charged"])
        raw = float(row["Raw Hours"])
        cat = "production" if user in PROD_USERS else "other"
        key = (date, host, cat)
        data[key]["charged"] += charged
        data[key]["raw"] += raw
        total_key = (date, host, "total")
        data[total_key]["charged"] += charged
        data[total_key]["raw"] += raw
    return data


def format_summaries(rows, label):
    """Build summary text. Returns string."""
    lines = []
    lines.append(f"{'=' * 70}")
    lines.append(f"Summary for: {label}")
    lines.append(f"{'=' * 70}")
    lines.append("")

    # totals by host type
    by_host = defaultdict(lambda: {"charged": 0.0, "raw": 0.0})
    for row in rows:
        host = row["Host Name"]
        by_host[host]["charged"] += float(row["Node Hours Charged"])
        by_host[host]["raw"] += float(row["Raw Hours"])

    lines.append("Total Node Hours by Host Type")
    lines.append(f"{'Host':<20} {'Charged':>12} {'Raw':>12}")
    lines.append("-" * 50)
    for host in sorted(by_host):
        lines.append(f"{host:<20} {by_host[host]['charged']:>12.1f} {by_host[host]['raw']:>12.1f}")
    lines.append("")

    # top users of perlmutter gpu
    gpu_users = defaultdict(lambda: {"charged": 0.0, "raw": 0.0})
    for row in rows:
        if row["Host Name"] == "perlmutter gpu":
            user = row["User"]
            gpu_users[user]["charged"] += float(row["Node Hours Charged"])
            gpu_users[user]["raw"] += float(row["Raw Hours"])

    lines.append("Top Users of Perlmutter GPU (by Charged Node Hours)")
    lines.append(f"{'User':<40} {'Charged':>12} {'Raw':>12}")
    lines.append("-" * 65)
    for user, vals in sorted(gpu_users.items(), key=lambda x: -x[1]["charged"]):
        lines.append(f"{user:<40} {vals['charged']:>12.1f} {vals['raw']:>12.1f}")
    lines.append("")

    # periodic totals for perlmutter gpu (monthly or daily)
    gpu_periodic = defaultdict(lambda: {"charged": 0.0, "raw": 0.0})
    for row in rows:
        if row["Host Name"] == "perlmutter gpu":
            date = row["Date"]
            gpu_periodic[date]["charged"] += float(row["Node Hours Charged"])
            gpu_periodic[date]["raw"] += float(row["Raw Hours"])

    period = "Period"
    lines.append(f"Perlmutter GPU Totals by {period}")
    lines.append(f"{period:<15} {'Charged':>12} {'Raw':>12}")
    lines.append("-" * 45)
    for date in sorted(gpu_periodic):
        lines.append(f"{date:<15} {gpu_periodic[date]['charged']:>12.1f} {gpu_periodic[date]['raw']:>12.1f}")
    lines.append("")

    return "\n".join(lines)


def plot_host(data, host, outname, label, period):
    """Plot charged vs raw for a given host, split by production/other."""
    dates_set = set()
    for (d, h, c) in data:
        if h == host:
            dates_set.add(d)
    dates_str = sorted(dates_set)
    if not dates_str:
        print(f"  No data for host '{host}'")
        return

    dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates_str]

    def get_series(category, field):
        return [data.get((d, host, category), {"charged": 0, "raw": 0})[field] for d in dates_str]

    total_charged = get_series("total", "charged")
    total_raw = get_series("total", "raw")
    prod_charged = get_series("production", "charged")
    prod_raw = get_series("production", "raw")
    other_charged = get_series("other", "charged")
    other_raw = get_series("other", "raw")

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(dates, total_charged, 'k-', linewidth=2, label="Total (charged)")
    ax.plot(dates, total_raw, 'k--', linewidth=2, label="Total (raw)")
    ax.plot(dates, prod_charged, 'b-', linewidth=1.5, label="Production (charged)")
    ax.plot(dates, prod_raw, 'b--', linewidth=1.5, label="Production (raw)")
    ax.plot(dates, other_charged, 'r-', linewidth=1.5, label="Other (charged)")
    ax.plot(dates, other_raw, 'r--', linewidth=1.5, label="Other (raw)")

    ax.set_xlabel("Date")
    ax.set_ylabel("Node Hours")
    ax.set_title(f"NERSC {host} — DUNE {label}")

    if period == "daily":
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())

    fig.autofmt_xdate()
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(outname, dpi=150)
    print(f"  Saved {outname}")
    plt.close()


def run_variant(period, project):
    """Run analysis for one (period, project) combination."""
    key = (period, project)
    if key not in VARIANTS:
        print(f"Unknown variant: {period} {project}")
        return

    filename = os.path.join(DATADIR, VARIANTS[key])
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return

    label = f"({project}, {period})"
    outdir = f"output_{period}_{project}"
    os.makedirs(outdir, exist_ok=True)

    print(f"\nProcessing {label} from {filename}")
    print(f"  Output directory: {outdir}/")

    rows = read_data(filename)

    # summaries -> stdout and text file
    summary = format_summaries(rows, label)
    print(summary)
    stats_file = os.path.join(outdir, f"stats_{period}_{project}.txt")
    with open(stats_file, "w") as f:
        f.write(summary)
    print(f"  Saved {stats_file}")

    # plots
    data = aggregate(rows)
    hosts = sorted(set(row["Host Name"] for row in rows))

    # perlmutter gpu first
    if "perlmutter gpu" in hosts:
        plot_host(data, "perlmutter gpu",
                  os.path.join(outdir, "perlmutter_gpu.png"), label, period)

    for host in hosts:
        if host == "perlmutter gpu":
            continue
        safe = host.replace(" ", "_")
        plot_host(data, host,
                  os.path.join(outdir, f"{safe}.png"), label, period)


def main():
    parser = argparse.ArgumentParser(
        description="Plot NERSC DUNE usage from IRIS report CSVs")
    parser.add_argument("period", nargs="?", choices=["daily", "monthly"],
                        help="daily or monthly (default: both)")
    parser.add_argument("project", nargs="?", choices=["dune", "m3249"],
                        help="project name (default: both)")
    args = parser.parse_args()

    if args.period and args.project:
        run_variant(args.period, args.project)
    elif args.period:
        for proj in ["dune", "m3249"]:
            run_variant(args.period, proj)
    elif args.project:
        for per in ["monthly", "daily"]:
            run_variant(per, args.project)
    else:
        for (per, proj) in sorted(VARIANTS.keys()):
            run_variant(per, proj)


if __name__ == "__main__":
    main()
