#!/usr/bin/env python3
"""DUNE Computing Model — standalone script replacing the notebook.

Reads the JSON config for projections, reads NERSC IRIS CSVs for actuals,
and produces combined plots and summaries.

All GPU quantities are in GPU Node Hours (Perlmutter: 4 A100s per node).
All CPU quantities are in CPU Node Hours (Perlmutter: varies).
Model projections are converted from their native MHrs to node hours for
comparison with NERSC actuals.

Usage:
    python computing_model.py [--config CONFIG.json] [--outdir DIR]
"""

import argparse
import csv
import math
import os
import sys
from collections import defaultdict
from datetime import datetime

import commentjson
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# ---------------------------------------------------------------------------
# NERSC configuration
# ---------------------------------------------------------------------------

NERSC_DATA_DIR = "data"
NERSC_FILES = {
    "daily_dune": "nersc_daily_report_project_dune_2025.csv",
    "daily_m3249": "nersc_daily_report_project_m3249_2025.csv",
    "monthly_dune": "nersc_monthly_report_project_dune_2025.csv",
    "monthly_m3249": "nersc_monthly_report_project_m3249_2025.csv",
}

PROD_USERS = {"Pseudo User, dunepr", "Pseudo User, dunepro"}

# Perlmutter GPU node: 4 A100 GPUs
GPUS_PER_NODE = 4

# ---------------------------------------------------------------------------
# Calibrated production rates from the big 2025 run
#
# Source: 122 NERSC GPU Node Hours / 1e18 POT for full-spill FHC+RHC
# This is the key measured rate we use to project GPU needs from POT.
#
# The production run (~2025-09-28 to 2026-02) produced:
#   - 1e19 POT FHC + 1e19 POT RHC full spill  (O(millions) interactions)
#   - 1e22 POT nu-on-e elastic scattering singles FHC+RHC (O(1000-10000) spills)
# CPU ran on project "dune", GPU on project "m3249"
# ---------------------------------------------------------------------------

CALIBRATION = {
    "gpu_node_hrs_per_1e18_pot": 122.0,  # measured from full-spill production
    "pot_per_spill": 7.5e13,
}

PROD_RUN = {
    "start": "2025-09-28",
    "end": "2026-02-01",
    "full_spill_pot": 2e19,  # 1e19 FHC + 1e19 RHC
    "nue_elastic_pot": 1e22,  # special sample
    "cpu_project": "dune",
    "cpu_host": "perlmutter cpu",
    "gpu_project": "m3249",
    "gpu_host": "perlmutter gpu",
}


# ---------------------------------------------------------------------------
# Model functions (from NumberUtils.py / notebook)
# ---------------------------------------------------------------------------

def cumulate_map(years, a, lifetime=100):
    """Sum backwards over lifetime of record."""
    lifetimebase = math.floor(lifetime)
    lifetimeextra = lifetime - lifetimebase
    b = {y: 0.0 for y in years}
    for i in years:
        begin = max(years[0], i - lifetimebase + 1)
        for j in range(begin, i + 1):
            b[i] += a[j]
        if lifetimeextra > 0 and begin > years[0]:
            b[i] += a[begin - 1] * lifetimeextra
    return b


def extend_map(years, a, lifetime=0):
    """Extend non-zero values forward."""
    b = {y: a[y] for y in years}
    lifetimebase = math.floor(lifetime)
    for i in years:
        if a[i] != 0:
            continue
        for j in range(1, lifetimebase + 1):
            if i - j < years[0]:
                continue
            if a[i - j] != 0:
                b[i] = a[i - j]
                break
    return b


# ---------------------------------------------------------------------------
# Read JSON config and compute projections
# ---------------------------------------------------------------------------

def load_config(filename):
    with open(filename, 'r') as f:
        return commentjson.load(f)


def compute_projections(config):
    """Replicate the notebook's projection calculations.

    Returns Data dict: Data[dtype][det][year] = value
    Units are as in the JSON (MHrs for CPU/GPU, PB for storage, M for events).
    """
    Years = config["Years"]
    Detectors = config["Detectors"]
    BaseMemory = config["Base-Memory"]
    MWCWeight = config["MWCWeight"]
    Reprocess = config["Reprocess"]
    AnalysisExtend = config["AnalysisExtend"]
    PerYear = config["PerYear"]
    Units = config["Units"]

    if not MWCWeight:
        for det in Detectors:
            config[det]["Reco-Memory"] = BaseMemory
            config[det]["Sim-Memory"] = BaseMemory

    dofirst = ["Events", "Test", "Sim-Events"]

    Inputs = {}
    for det in Detectors:
        Inputs[det] = {}
        for dtype in dofirst:
            Inputs[det][dtype] = {}
            for year in Years:
                Inputs[det][dtype][year] = float(config[det][dtype][year - Years[0]])

    DetectorParameters = [k for k in config["SP"].keys() if k != "Comment"]

    for det in Detectors:
        for key in DetectorParameters:
            if key in dofirst:
                continue

            if key in ["Reco-Data-CPU", "Reco-Data-GPU", "Reco-Data-Store"]:
                Inputs[det][key] = cumulate_map(Years, Inputs[det]["Events"], Reprocess[det])
                for year in Years:
                    Inputs[det][key][year] *= config[det][key]
                if key == "Reco-Data-CPU" and MWCWeight:
                    for year in Years:
                        Inputs[det][key][year] *= (config[det]["Reco-Memory"] / BaseMemory)
                continue

            if key == "Raw-Store":
                Inputs[det][key] = {}
                for year in Years:
                    Inputs[det][key][year] = Inputs[det]["Events"][year] * config[det][key]
                continue

            if key in ["Sim-Store", "Sim-CPU", "Sim-GPU"]:
                Inputs[det][key] = {}
                for year in Years:
                    Inputs[det][key][year] = Inputs[det]["Sim-Events"][year] * config[det][key]
                    if key == "Sim-CPU" and MWCWeight:
                        Inputs[det][key][year] *= (config[det]["Sim-Memory"] / BaseMemory)
                if key in ["Sim-Store"]:
                    Inputs[det][key] = extend_map(Years, Inputs[det][key], AnalysisExtend)
                continue

            if key in ["Analysis-CPU"]:
                data_ext = extend_map(Years, Inputs[det]["Reco-Data-CPU"], AnalysisExtend)
                mc_ext = extend_map(Years, Inputs[det]["Sim-CPU"], AnalysisExtend)
                Inputs[det][key] = {}
                for year in Years:
                    Inputs[det][key][year] = (data_ext[year] + mc_ext[year]) * config[det]["Analysis-CPU"]
                continue

    for det in Detectors:
        Inputs[det].pop("Sim-Memory", None)
        Inputs[det].pop("Reco-Memory", None)

    # Apply PerYear and unit conversion
    Data = {}
    fields = [k for k in Inputs[Detectors[0]].keys() if "Memory" not in k]
    for dtype in fields:
        Data[dtype] = {}
        for det in Detectors:
            Data[dtype][det] = {}
            for year in Years:
                val = Inputs[det][dtype][year] * float(PerYear.get(dtype, 1))
                if Units.get(dtype) == "PB":
                    val *= 0.001
                Data[dtype][det][year] = val

    # Cap raw store
    Data["Raw-Store"]["Total"] = {}
    Cap = config["Cap"]
    for year in Years:
        Data["Raw-Store"]["Total"][year] = sum(Data["Raw-Store"][det][year] for det in Detectors)
    for det in Detectors:
        for year in Years:
            cap = Data["Raw-Store"]["Total"][year] / Cap
            if cap > 1:
                Data["Raw-Store"][det][year] /= cap

    # Merge protodunes and far detectors
    for dtype in list(Data.keys()):
        Data[dtype]["PDs"] = {}
        for year in Years:
            Data[dtype]["PDs"][year] = sum(Data[dtype][d][year] for d in ["SP", "DP", "PDHD", "PDVD"])
        for d in ["SP", "DP", "PDHD", "PDVD"]:
            Data[dtype].pop(d)

        Data[dtype]["FDs"] = {}
        for year in Years:
            Data[dtype]["FDs"][year] = sum(Data[dtype][d][year] for d in ["HD", "VD"])
        for d in ["HD", "VD"]:
            Data[dtype].pop(d)

    # Totals across detectors
    CombinedDetectors = config["CombinedDetectors"]
    for dtype in list(Data.keys()):
        Data[dtype]["Total"] = {}
        for year in Years:
            Data[dtype]["Total"][year] = sum(
                Data[dtype][det][year] for det in Data[dtype] if det != "Total"
            )

    # Total-CPU and Total-GPU
    for total_key, components in [
        ("Total-CPU", ["Reco-Data-CPU", "Sim-CPU", "Analysis-CPU"]),
        ("Total-GPU", ["Reco-Data-GPU", "Sim-GPU"]),
    ]:
        Data[total_key] = {}
        for det in CombinedDetectors:
            Data[total_key][det] = {}
            for year in Years:
                Data[total_key][det][year] = sum(Data[c][det][year] for c in components)
        Data[total_key]["Total"] = {}
        for year in Years:
            Data[total_key]["Total"][year] = sum(
                Data[total_key][det][year] for det in CombinedDetectors
            )

    # Cores, HS23, Wall
    efficiency = config["Cores"]["Efficiency"]
    scaleTo2020 = config["Cores"]["2020Units"]
    MHrsPerYear = 1_000_000 / 365.0 / 24.0

    for derived in ["Cores", "HS23", "Wall"]:
        Data[derived] = {}
    for k in Data["Total-CPU"]:
        for derived in ["Cores", "HS23", "Wall"]:
            Data[derived][k] = {}
        for year in Years:
            cpu = Data["Total-CPU"][k][year]
            Data["Wall"][k][year] = cpu / scaleTo2020 / efficiency
            Data["Cores"][k][year] = cpu * MHrsPerYear / scaleTo2020 / efficiency
            Data["HS23"][k][year] = (
                cpu * MHrsPerYear / scaleTo2020 / efficiency * config["kHEPSPEC06PerCPU"]
            )

    return Data


# ---------------------------------------------------------------------------
# NERSC actual data
# ---------------------------------------------------------------------------

def read_nersc_csv(filename):
    """Read a NERSC IRIS CSV, return list of row dicts with normalized Date."""
    rows = []
    with open(filename, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if "Day" in row:
                row["Date"] = row["Day"]
            elif "Month" in row:
                row["Date"] = row["Month"]
            rows.append(row)
    return rows


def load_nersc_actuals():
    """Load all available NERSC data, return structured dict."""
    actuals = {}
    for key, fn in NERSC_FILES.items():
        path = os.path.join(NERSC_DATA_DIR, fn)
        if os.path.exists(path):
            actuals[key] = read_nersc_csv(path)
    return actuals


def aggregate_nersc_monthly(actuals):
    """Aggregate NERSC data into monthly totals by host and category.

    Returns dict: result[project][host][month] -> {prod_charged, prod_raw,
                                                    other_charged, other_raw,
                                                    total_charged, total_raw}
    """
    result = {}
    for key in ["monthly_dune", "monthly_m3249"]:
        if key not in actuals:
            continue
        project = key.split("_")[1]
        result[project] = defaultdict(lambda: defaultdict(
            lambda: {"prod_charged": 0, "prod_raw": 0,
                     "other_charged": 0, "other_raw": 0,
                     "total_charged": 0, "total_raw": 0}
        ))
        for row in actuals[key]:
            host = row["Host Name"]
            month = row["Date"]
            charged = float(row["Node Hours Charged"])
            raw = float(row["Raw Hours"])
            is_prod = row["User"] in PROD_USERS
            result[project][host][month]["total_charged"] += charged
            result[project][host][month]["total_raw"] += raw
            if is_prod:
                result[project][host][month]["prod_charged"] += charged
                result[project][host][month]["prod_raw"] += raw
            else:
                result[project][host][month]["other_charged"] += charged
                result[project][host][month]["other_raw"] += raw
    return result


def compute_prod_run_actuals(actuals):
    """Extract actual node hours during the production run window."""
    run = PROD_RUN

    cpu_total = 0.0
    gpu_total = 0.0

    daily_cpu_key = f"daily_{run['cpu_project']}"
    if daily_cpu_key in actuals:
        for row in actuals[daily_cpu_key]:
            if (row["Host Name"] == run["cpu_host"]
                    and row["User"] in PROD_USERS
                    and run["start"] <= row["Date"] <= run["end"]):
                cpu_total += float(row["Node Hours Charged"])

    daily_gpu_key = f"daily_{run['gpu_project']}"
    if daily_gpu_key in actuals:
        for row in actuals[daily_gpu_key]:
            if (row["Host Name"] == run["gpu_host"]
                    and row["User"] in PROD_USERS
                    and run["start"] <= row["Date"] <= run["end"]):
                gpu_total += float(row["Node Hours Charged"])

    return {
        "cpu_node_hrs": cpu_total,
        "gpu_node_hrs": gpu_total,
    }


def annualize_nersc(nersc_monthly, host, projects=None, field="total_charged"):
    """Sum monthly node hours into annual totals across projects.

    Returns dict: {year: node_hours}
    """
    if projects is None:
        projects = list(nersc_monthly.keys())
    by_year = defaultdict(float)
    for proj in projects:
        if proj not in nersc_monthly:
            continue
        if host not in nersc_monthly[proj]:
            continue
        for month, vals in nersc_monthly[proj][host].items():
            dt = datetime.strptime(month, "%Y-%m-%d")
            by_year[dt.year] += vals[field]
    return dict(by_year)


def monthly_series(nersc_monthly, host, projects=None, field="total_charged"):
    """Combine monthly node hours across projects for a given host.

    Returns dict: {month_str: node_hours}
    """
    if projects is None:
        projects = list(nersc_monthly.keys())
    result = defaultdict(float)
    for proj in projects:
        if proj not in nersc_monthly:
            continue
        if host not in nersc_monthly[proj]:
            continue
        for month, vals in nersc_monthly[proj][host].items():
            result[month] += vals[field]
    return dict(result)


# ---------------------------------------------------------------------------
# Unit conversion: model MHrs -> GPU/CPU node hours
# ---------------------------------------------------------------------------

def model_gpu_mhrs_to_node_hrs(mhrs):
    """Convert model GPU MHrs to GPU node hours.

    The model GPU unit is "GPU MHrs" (millions of GPU-hours).
    A Perlmutter GPU node has 4 GPUs.
    1 MHrs = 1e6 GPU-hours = 1e6/4 = 250,000 GPU node hours.
    """
    return mhrs * 1e6 / GPUS_PER_NODE


def model_cpu_mhrs_to_node_hrs(mhrs, cores_per_node=128):
    """Convert model CPU MHrs to CPU node hours.

    The model CPU unit is "CPU MHrs" (millions of CPU core-hours).
    Perlmutter CPU node has 128 cores (AMD Milan).
    1 MHrs = 1e6 core-hours = 1e6/128 node hours.
    """
    return mhrs * 1e6 / cores_per_node


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_model_vs_actual(
    years, projections_by_det, actual_annual,
    actual_monthly, title, ylabel, outpath,
    det_colors=None, combined_detectors=None,
):
    """Plot model projections (converted to node hrs) + NERSC actuals."""
    fig, (ax_main, ax_zoom) = plt.subplots(1, 2, figsize=(16, 6),
                                            gridspec_kw={"width_ratios": [2, 1]})

    for ax in [ax_main, ax_zoom]:
        # model projections
        for det in (combined_detectors or []) + ["Total"]:
            if det not in projections_by_det:
                continue
            ys = [projections_by_det[det].get(y, 0) for y in years]
            color = det_colors.get(det, None) if det_colors else None
            ls = "dashed" if det == "Total" else "solid"
            lw = 2 if det == "Total" else 1.2
            ax.plot(years, ys, color=color, linestyle=ls, linewidth=lw,
                    label=f"Model {det}")

        # annual actuals as bars
        if actual_annual:
            act_years = sorted(actual_annual.keys())
            act_vals = [actual_annual[y] for y in act_years]
            ax.bar(act_years, act_vals, width=0.4, alpha=0.4, color="green",
                   label="NERSC Actual (annual)", zorder=5)

        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    # main: full range
    ax_main.set_xlim(years[0], years[-1])
    ax_main.set_title(title)
    ax_main.legend(frameon=False, fontsize=8)

    # zoom: recent years only
    zoom_min = 2024
    zoom_max = 2030
    ax_zoom.set_xlim(zoom_min, zoom_max)
    ax_zoom.set_title(f"{title} (zoom {zoom_min}–{zoom_max})")

    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    print(f"  Saved {outpath}")
    plt.close()


def plot_monthly_actual(nersc_monthly, host, projects, outpath, title):
    """Plot monthly NERSC node hours for a host, split by prod/other."""
    months_set = set()
    for proj in projects:
        if proj in nersc_monthly and host in nersc_monthly[proj]:
            months_set.update(nersc_monthly[proj][host].keys())
    if not months_set:
        return

    months = sorted(months_set)
    dates = [datetime.strptime(m, "%Y-%m-%d") for m in months]

    prod = []
    other = []
    total = []
    for m in months:
        p = o = t = 0
        for proj in projects:
            if proj in nersc_monthly and host in nersc_monthly[proj]:
                vals = nersc_monthly[proj][host].get(m, {})
                p += vals.get("prod_charged", 0)
                o += vals.get("other_charged", 0)
                t += vals.get("total_charged", 0)
        prod.append(p)
        other.append(o)
        total.append(t)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, total, 'k-', linewidth=2, label="Total")
    ax.plot(dates, prod, 'b-', linewidth=1.5, label="Production")
    ax.plot(dates, other, 'r-', linewidth=1.5, label="Other users")
    ax.set_xlabel("Date")
    ax.set_ylabel("Node Hours (charged)")
    ax.set_title(title)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate()
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    print(f"  Saved {outpath}")
    plt.close()


# ---------------------------------------------------------------------------
# Summary text
# ---------------------------------------------------------------------------

def format_calibration_summary(prod_run_actuals):
    cal = CALIBRATION
    run = PROD_RUN
    lines = []
    lines.append("=" * 70)
    lines.append("Production Run & Calibration")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Period: {run['start']} to {run['end']}")
    lines.append(f"  Full-spill POT: {run['full_spill_pot']:.0e} (1e19 FHC + 1e19 RHC)")
    lines.append(f"  nu-on-e elastic POT: {run['nue_elastic_pot']:.0e} (special sample)")
    lines.append("")
    lines.append(f"  Calibrated rate: {cal['gpu_node_hrs_per_1e18_pot']} GPU node hrs / 1e18 POT")
    lines.append(f"    = {cal['gpu_node_hrs_per_1e18_pot'] * GPUS_PER_NODE:.0f} GPU-hrs / 1e18 POT")
    spills_per_1e18 = 1e18 / cal["pot_per_spill"]
    lines.append(f"    = {cal['gpu_node_hrs_per_1e18_pot'] / spills_per_1e18:.4f} "
                 f"GPU node hrs/spill ({spills_per_1e18:.0f} spills per 1e18 POT)")
    lines.append("")
    lines.append("  Measured NERSC usage during production window:")
    lines.append(f"    CPU (project {run['cpu_project']}, {run['cpu_host']}): "
                 f"{prod_run_actuals['cpu_node_hrs']:.1f} node hrs")
    lines.append(f"    GPU (project {run['gpu_project']}, {run['gpu_host']}): "
                 f"{prod_run_actuals['gpu_node_hrs']:.1f} node hrs")
    lines.append("")
    expected_full_spill = run["full_spill_pot"] / 1e18 * cal["gpu_node_hrs_per_1e18_pot"]
    lines.append(f"  Expected GPU for full-spill: {expected_full_spill:.0f} node hrs "
                 f"(from {run['full_spill_pot']:.0e} POT)")
    lines.append(f"  Remainder for nu-on-e + other: "
                 f"{prod_run_actuals['gpu_node_hrs'] - expected_full_spill:.0f} node hrs")
    lines.append("=" * 70)
    return "\n".join(lines)


def format_annual_summary(Data, years, nersc_monthly):
    """Annual model vs actuals, all in node hours."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("Annual Summary: Model vs NERSC Actuals")
    lines.append("All values in Node Hours")
    lines.append("=" * 70)

    # GPU
    gpu_annual = annualize_nersc(nersc_monthly, "perlmutter gpu")
    lines.append("")
    lines.append("GPU (Perlmutter GPU Node Hours)")
    lines.append(f"{'Year':<8} {'Model':>12} {'NERSC':>12} {'Ratio':>8}")
    lines.append("-" * 45)
    for year in years:
        model_mhrs = Data["Total-GPU"]["Total"].get(year, 0)
        model_nh = model_gpu_mhrs_to_node_hrs(model_mhrs)
        actual = gpu_annual.get(year, 0)
        if actual > 0 and model_nh > 0:
            ratio = f"{actual / model_nh:>8.2f}"
        elif actual > 0:
            ratio = f"{'inf':>8}"
        else:
            ratio = f"{'—':>8}"
        actual_s = f"{actual:>12.0f}" if actual > 0 else f"{'—':>12}"
        lines.append(f"{year:<8} {model_nh:>12.0f} {actual_s} {ratio}")

    # CPU
    cpu_annual = annualize_nersc(nersc_monthly, "perlmutter cpu")
    lines.append("")
    lines.append("CPU (Perlmutter CPU Node Hours, model assumes 128 cores/node)")
    lines.append(f"{'Year':<8} {'Model':>12} {'NERSC':>12} {'Ratio':>8}")
    lines.append("-" * 45)
    for year in years:
        model_mhrs = Data["Total-CPU"]["Total"].get(year, 0)
        model_nh = model_cpu_mhrs_to_node_hrs(model_mhrs)
        actual = cpu_annual.get(year, 0)
        if actual > 0 and model_nh > 0:
            ratio = f"{actual / model_nh:>8.2f}"
        elif actual > 0:
            ratio = f"{'inf':>8}"
        else:
            ratio = f"{'—':>8}"
        actual_s = f"{actual:>12.0f}" if actual > 0 else f"{'—':>12}"
        lines.append(f"{year:<8} {model_nh:>12.0f} {actual_s} {ratio}")

    lines.append("")
    lines.append("Note: Model projections are for ALL sites, not just NERSC.")
    lines.append("      NERSC is a fraction of total DUNE computing.")
    lines.append(f"      GPU model: 1 MHrs = {1e6/GPUS_PER_NODE:.0f} GPU node hrs "
                 f"({GPUS_PER_NODE} GPUs/node)")
    lines.append(f"      CPU model: 1 MHrs = {1e6/128:.0f} CPU node hrs (128 cores/node)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="DUNE Computing Model")
    parser.add_argument("--config", default="DOE23-NDLAr_2023-12-11-2040.json",
                        help="JSON config file")
    parser.add_argument("--outdir", default="model_output",
                        help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # --- Load config and compute projections ---
    print(f"Loading config: {args.config}")
    config = load_config(args.config)
    Years = config["Years"]
    MinYear = config["MinYear"]
    MaxYear = config["MaxYear"]
    PlotYears = list(range(MinYear, MaxYear + 1))
    CombinedDetectors = config["CombinedDetectors"]
    DetColors = config["DetColors"]

    print("Computing projections...")
    Data = compute_projections(config)

    # --- Load NERSC actuals ---
    print("Loading NERSC data...")
    actuals = load_nersc_actuals()
    nersc_monthly = aggregate_nersc_monthly(actuals)

    # --- Production run calibration ---
    print("Analyzing production run...")
    prod_run_actuals = compute_prod_run_actuals(actuals)
    cal_summary = format_calibration_summary(prod_run_actuals)
    print(cal_summary)

    # --- Annual summary ---
    annual_summary = format_annual_summary(Data, PlotYears, nersc_monthly)
    print(annual_summary)

    # --- Write stats ---
    stats_path = os.path.join(args.outdir, "summary.txt")
    with open(stats_path, "w") as f:
        f.write(cal_summary)
        f.write("\n")
        f.write(annual_summary)
    print(f"\n  Saved {stats_path}")

    # --- Plots: Model vs Actual (same units) ---
    print("\nGenerating plots...")

    # Convert model GPU projections to node hours for plotting
    gpu_model_nh = {}
    for det in list(Data["Total-GPU"].keys()):
        gpu_model_nh[det] = {y: model_gpu_mhrs_to_node_hrs(v)
                             for y, v in Data["Total-GPU"][det].items()}

    gpu_annual = annualize_nersc(nersc_monthly, "perlmutter gpu")
    plot_model_vs_actual(
        PlotYears, gpu_model_nh, gpu_annual, None,
        "Total GPU — Model vs NERSC Actual",
        "GPU Node Hours",
        os.path.join(args.outdir, "total_gpu_model_vs_actual.png"),
        det_colors=DetColors,
        combined_detectors=CombinedDetectors,
    )

    # Convert model CPU projections to node hours
    cpu_model_nh = {}
    for det in list(Data["Total-CPU"].keys()):
        cpu_model_nh[det] = {y: model_cpu_mhrs_to_node_hrs(v)
                             for y, v in Data["Total-CPU"][det].items()}

    cpu_annual = annualize_nersc(nersc_monthly, "perlmutter cpu")
    plot_model_vs_actual(
        PlotYears, cpu_model_nh, cpu_annual, None,
        "Total CPU — Model vs NERSC Actual",
        "CPU Node Hours",
        os.path.join(args.outdir, "total_cpu_model_vs_actual.png"),
        det_colors=DetColors,
        combined_detectors=CombinedDetectors,
    )

    # Model-only projections in native units
    for dtype in ["Reco-Data-GPU", "Sim-GPU", "Reco-Data-CPU", "Sim-CPU",
                  "Analysis-CPU", "Total-CPU", "Total-GPU"]:
        fig, ax = plt.subplots(figsize=(12, 6))
        for det in CombinedDetectors + ["Total"]:
            if det not in Data[dtype]:
                continue
            ys = [Data[dtype][det].get(y, 0) for y in PlotYears]
            color = DetColors.get(det, None)
            ls = "dashed" if det == "Total" else "solid"
            lw = 2 if det == "Total" else 1.2
            ax.plot(PlotYears, ys, color=color, linestyle=ls, linewidth=lw,
                    label=det)
        ax.set_xlabel("Year")
        ax.set_ylabel(config["Units"].get(dtype, dtype))
        ax.set_title(f"{dtype} — Model Projections")
        ax.legend(frameon=False, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(PlotYears[0], PlotYears[-1])
        plt.tight_layout()
        outpath = os.path.join(args.outdir, f"{dtype.replace(' ', '_')}.png")
        plt.savefig(outpath, dpi=150)
        print(f"  Saved {outpath}")
        plt.close()

    # NERSC monthly detail plots (combined across projects)
    for host in ["perlmutter gpu", "perlmutter cpu"]:
        safe = host.replace(" ", "_")
        plot_monthly_actual(
            nersc_monthly, host, ["dune", "m3249"],
            os.path.join(args.outdir, f"nersc_{safe}_monthly_combined.png"),
            f"NERSC {host} — All DUNE projects combined",
        )

    # Per-project monthly
    for proj in ["dune", "m3249"]:
        if proj not in nersc_monthly:
            continue
        for host in ["perlmutter gpu", "perlmutter cpu"]:
            safe = f"nersc_{proj}_{host.replace(' ', '_')}_monthly.png"
            plot_monthly_actual(
                nersc_monthly, host, [proj],
                os.path.join(args.outdir, safe),
                f"NERSC {host} — project {proj}",
            )

    print("\nDone.")


if __name__ == "__main__":
    main()
