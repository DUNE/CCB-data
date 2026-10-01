#!/usr/bin/env python3
"""POT-based GPU model for DUNE ND-LAr/TMS production.

This is intentionally separate from computing_model.py. The old model stores
GPU as per-event rates; this one uses full-spill POT as the primary axis.
Annual event counts are only used as a relative scaling proxy, not reported as
the model quantity.
"""

import argparse
import csv
import os

import commentjson


DEFAULT_SAMPLE_FACTORS = {
    # Relative to nominal full-spill work per POT.
    "nominal_full_spill": 1.0,
    "nue_singles": 0.002 / 122.0,
    "nue_overlay": 1.0,
    "systematic_full_spill": 1.0,
}


def load_config(path):
    with open(path) as f:
        return commentjson.load(f)


def parse_sample_args(sample_args):
    if not sample_args:
        return {"nominal_full_spill": 1.0}

    samples = {}
    for item in sample_args:
        if "=" not in item:
            raise ValueError(f"sample must look like name=multiplier, got {item!r}")
        name, value = item.split("=", 1)
        if name not in DEFAULT_SAMPLE_FACTORS:
            known = ", ".join(sorted(DEFAULT_SAMPLE_FACTORS))
            raise ValueError(f"unknown sample {name!r}; known samples: {known}")
        samples[name] = float(value)
    return samples


def annual_scales_from_events(config, detector, event_field, baseline_year):
    years = config["Years"]
    values_millions = config[detector][event_field]
    if baseline_year not in years:
        raise ValueError(f"baseline year {baseline_year} is not in config Years")
    baseline_value = float(values_millions[years.index(baseline_year)])
    if baseline_value <= 0:
        raise ValueError(
            f"baseline year {baseline_year} has non-positive {event_field}: {baseline_value}"
        )

    rows = []
    for year, value_millions in zip(years, values_millions):
        scale = float(value_millions) / baseline_value
        rows.append({
            "year": year,
            "scale_vs_baseline": scale,
        })
    return rows


def compute_gpu(rows, samples, baseline_pot_e18, full_spill_rate, empirical_scale):
    relative_work = sum(DEFAULT_SAMPLE_FACTORS[name] * multiplier
                        for name, multiplier in samples.items())
    for row in rows:
        row["full_spill_pot_e18"] = row["scale_vs_baseline"] * baseline_pot_e18
        row["sample_relative_work"] = relative_work
        row["gpu_node_hours"] = (
            row["full_spill_pot_e18"] * full_spill_rate * relative_work * empirical_scale
        )
        row["gpu_hours"] = row["gpu_node_hours"] * 4.0
    return rows


def write_csv(path, rows):
    fieldnames = [
        "year",
        "scale_vs_baseline",
        "full_spill_pot_e18",
        "sample_relative_work",
        "gpu_node_hours",
        "gpu_hours",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})


def format_summary(args, samples, rows):
    lines = []
    lines.append("# POT-Based GPU Model")
    lines.append("")
    lines.append(f"Config: `{args.config}`")
    lines.append(f"Detector: `{args.detector}`")
    lines.append(f"Internal scaling field: `{args.event_field}`")
    lines.append("")
    lines.append("## Normalization")
    lines.append("")
    lines.append(f"- Baseline year: {args.baseline_year}")
    lines.append(f"- Baseline full-spill POT: {args.baseline_pot_e18:g}e18 POT")
    lines.append(f"- Full-spill GPU cost: {args.full_spill_rate:g} GPU node-hours / 1e18 POT")
    lines.append(f"- Empirical scale: {args.empirical_scale:g}")
    lines.append("- Event counts are used only for relative annual scaling and are not reported.")
    lines.append("")
    lines.append("## Sample Mix")
    lines.append("")
    for name, multiplier in samples.items():
        factor = DEFAULT_SAMPLE_FACTORS[name]
        lines.append(
            f"- {name}: multiplier {multiplier:g}, relative work {factor:g}, "
            f"contribution {multiplier * factor:g}"
        )
    lines.append("")
    lines.append("## Annual Estimate")
    lines.append("")
    lines.append("| Year | Scale vs baseline | Full-spill POT (1e18) | GPU node-hours | GPU-hours |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for row in rows:
        if row["scale_vs_baseline"] == 0 and row["gpu_node_hours"] == 0:
            continue
        lines.append(
            f"| {row['year']} | {row['scale_vs_baseline']:.3g} | "
            f"{row['full_spill_pot_e18']:.3g} | {row['gpu_node_hours']:.1f} | "
            f"{row['gpu_hours']:.1f} |"
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="POT-based ND-LAr/TMS GPU model")
    parser.add_argument("--config", default="DOE23-NDLAr_2023-12-11-2040.json")
    parser.add_argument("--detector", default="ND-LAr+TMS")
    parser.add_argument("--event-field", default="Sim-Events",
                        choices=["Events", "Sim-Events"])
    parser.add_argument("--baseline-year", type=int, default=2025)
    parser.add_argument("--baseline-pot-e18", type=float, default=2.0,
                        help="Full-spill POT in 1e18 units assigned to baseline year")
    parser.add_argument("--full-spill-rate", type=float, default=17992.1,
                        help="GPU node-hours per 1e18 POT for nominal full-spill work")
    parser.add_argument("--empirical-scale", type=float, default=1.0,
                        help="Optional correction from benchmark to observed accounting")
    parser.add_argument("--sample", action="append",
                        help="Sample multiplier, e.g. nominal_full_spill=1 or nue_overlay=2")
    parser.add_argument("--outdir", default="gpu_pot_model_output")
    args = parser.parse_args()

    config = load_config(args.config)
    samples = parse_sample_args(args.sample)
    rows = annual_scales_from_events(
        config, args.detector, args.event_field, args.baseline_year,
    )
    rows = compute_gpu(
        rows, samples, args.baseline_pot_e18,
        args.full_spill_rate, args.empirical_scale,
    )

    os.makedirs(args.outdir, exist_ok=True)
    write_csv(os.path.join(args.outdir, "annual_gpu_pot_model.csv"), rows)
    summary = format_summary(args, samples, rows)
    with open(os.path.join(args.outdir, "summary.md"), "w") as f:
        f.write(summary)
    print(summary)


if __name__ == "__main__":
    main()
