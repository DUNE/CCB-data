# GPU Model Notes

This note separates two related tasks:

1. Summarize the NERSC GPU usage stats and put them in context.
2. Decide how the long-term GPU model should scale with beam/exposure.

## NERSC GPU Usage Summary

Source files:

- `output_monthly_m3249/stats_monthly_m3249.txt`
- `output_monthly_dune/stats_monthly_dune.txt`
- `model_output/gpu_comparison_table.txt`

NERSC reports Perlmutter GPU usage in GPU node-hours. One Perlmutter GPU node
has four A100 GPUs, so literal GPU-hours are four times the GPU node-hours.

For project `m3249` on `perlmutter gpu`:

- Total: 20,622.2 charged node-hours; 21,333.9 raw node-hours.
- `Pseudo User, dunepro`: 20,602.8 charged node-hours; 21,314.6 raw node-hours.
- Other named users are tiny by comparison: Layne Sauer 13.8, Evan Brinckman
  2.7, Michael Wang 1.8, Meghna Bhattacharya 1.0 charged node-hours.

Monthly `m3249` Perlmutter GPU totals:

| Month | Charged node-hours | Raw node-hours |
| --- | ---: | ---: |
| 2025-08 | 486.4 | 486.4 |
| 2025-09 | 619.6 | 619.6 |
| 2025-10 | 268.8 | 268.8 |
| 2025-11 | 1,139.7 | 1,139.7 |
| 2025-12 | 11,351.9 | 11,351.9 |
| 2026-01 | 4,789.9 | 5,500.5 |

The hand summary called Nov-Jan the campaign core:

- Nov-Jan campaign core: 17,271 GPU node-hours.
- Aug-Jan full window: 18,639 GPU node-hours.

For project `dune` on `perlmutter gpu`:

- Total: 39,161.6 charged node-hours; 38,965.2 raw node-hours.
- Top charged users:
  - Kazuhiro Terao: 9,968.7
  - Madan Sharma Timalsina: 8,560.0
  - Callum Wilkinson: 7,532.6 charged; 6,654.8 raw
  - A.J. Nielsen: 3,167.7 charged; 3,836.9 raw
  - Roger Huang: 2,412.0

Annual Perlmutter GPU totals from the summary:

| Project | 2025 charged node-hours | 2026 charged node-hours, Jan only |
| --- | ---: | ---: |
| `dune` | 37,199 | 1,963 |
| `m3249` | 15,832 | 4,790 |
| Combined | 53,031 | 6,753 |

## Benchmark Context

The benchmark-derived rate in `model_output/gpu_comparison_table.txt` is:

- Nominal full-spill GPU: 122 GPU node-hours per 1e18 POT.
- This is 488 literal GPU-hours per 1e18 POT.
- Using 7.5e13 POT/spill, 1e18 POT is about 13,333 spills.
- That gives 0.00915 GPU node-hours/spill, or 0.0366 literal GPU-hours/spill
  (about 132 GPU-seconds/spill).

Jeff's Notion note says the benchmark sample was nominally 1e18 POT, with
2.56e18 GENIE fireworks configured. Jeff also noted:

- 136 reconstructed TMS events per spill.
- 1 spill = 7.50e13 POT.
- The TMS reconstructed event rate is probably about 2-3x larger than the
  ND-LAr event rate, so TMS events are an imperfect denominator for an ND-LAr
  GPU workload.

Using the nominal 1e18 POT denominator:

- spills: 13,333.333
- reconstructed TMS events: 1,813,333
- rate: 0.00006728 GPU node-hours/TMS event
- literal GPU rate: 0.0002691 GPU-hours/TMS event, or about 0.969 GPU-seconds/TMS event

Using the 2.56e18 configured-POT denominator:

- spills: 34,133.333
- reconstructed TMS events: 4,642,133
- rate: 0.00002628 GPU node-hours/TMS event
- literal GPU rate: 0.0001051 GPU-hours/TMS event, or about 0.378 GPU-seconds/TMS event

The produced sample estimate was:

- Expected from benchmark rates and actual POT: 4,920 GPU node-hours.
- Measured `m3249` production, Nov-Jan: 17,271 GPU node-hours.
- Ratio: 17,271 / 4,920 = 3.51.

So the benchmark-style estimate underpredicts the measured campaign by about
3.5x. Plausible reasons noted in the generated comparison were charge-only
benchmark vs possible light simulation, antifiducial reuse assumptions, retries,
campaign commissioning/debugging, and additional processing steps.

## What The Current JSON Model Is Doing

The JSON model uses `Events` and `Sim-Events` as annual counts in millions.
The code then multiplies those counts by per-event rates:

- `Reco-Data-GPU` is multiplied by cumulative `Events`.
- `Sim-GPU` is multiplied directly by `Sim-Events`.
- Output unit is `GPU MHrs`, i.e. millions of GPU-hours.

For `ND-LAr+TMS`, the current JSON values are:

- `Reco-Data-GPU = 0.76` GPU-hours/event.
- `Sim-GPU = 4.6` GPU-hours/event.
- Total GPU rate if combined naively: 5.36 GPU-hours/event.

Those numbers are much larger than the benchmark-implied per-spill and
per-interaction rates:

- Compared to 0.0366 GPU-hours/spill, 5.36 GPU-hours/event is about 146x larger.
- Compared to 0.00122 GPU-hours/interaction, 5.36 GPU-hours/event is about
  4,400x larger.

This is why the current JSON projection produces millions of GPU node-hours for
ND-LAr+TMS. The code is doing the unit conversion consistently given its inputs,
but the GPU per-event input is not a valid long-term scaling unit for the current
ND-LAr production model.

## Modeling Recommendation

For ND-LAr+TMS GPU needs, do not scale primarily by "literal interaction" count.
That is a poor predictor because:

- pileup means a spill contains multiple interactions;
- reconstruction/simulation cost is driven by full detector readout/context, not
  just countable final selected interactions;
- many rock muons pass outside the detectors and add little or no reco compute;
- overlay/full-spill context dominates special samples such as nu-on-e overlay.

The better long-term unit is a sample/exposure model:

- nominal full-spill samples scale with POT/spills;
- nu-on-e singles have their own tiny per-POT rate;
- nu-on-e + nominal overlay should use the full-spill/overlay rate, not the
  singles rate;
- systematics should be explicit replicas or fractional replicas of nominal
  full-spill production;
- apply an empirical correction factor, currently about 3.5x, only if the goal
  is to match observed campaign accounting rather than ideal benchmark rates.

In other words: the model should ask "how many spills / full-spill-equivalent
samples / overlay samples / systematic replicas are we producing?", not "how
many literal neutrino interactions are there?"

## First Conservative Scaled Trial

For a first pass, `DOE23-NDLAr_2023-12-11-2040.json` was changed so the
`ND-LAr+TMS` GPU per-event rates use the nominal 1e18 POT benchmark denominator:

- `Reco-Data-GPU = 0.00026912` GPU-hours/TMS reco event
- `Sim-GPU = 0.00026912` GPU-hours/TMS reco event

This is intentionally a placeholder. It keeps the old model structure but fixes
the scale. The benchmark really belongs in a sample/exposure model rather than
in a generic per-event field.

The standalone script was run as:

```bash
../myenv/bin/python computing_model.py \
  --config DOE23-NDLAr_2023-12-11-2040.json \
  --outdir model_output_scaled_1e18
```

The venv emitted a harmless path warning because the project was moved out of
the archive and the command used `../myenv/bin/python`, but the run completed.

Selected `ND-LAr+TMS` GPU node-hour results from the scaled trial:

| Year | Sim GPU node-hours | Reco-data GPU node-hours | Total GPU node-hours |
| --- | ---: | ---: | ---: |
| 2025 | 67.3 | 0.0 | 67.3 |
| 2026 | 336.4 | 0.0 | 336.4 |
| 2027 | 672.8 | 0.0 | 672.8 |
| 2028 | 1,345.6 | 0.0 | 1,345.6 |
| 2029 | 2,018.4 | 0.0 | 2,018.4 |
| 2030 | 3,027.6 | 0.0 | 3,027.6 |
| 2031 | 4,036.8 | 1,009.2 | 5,046.0 |
| 2035 | 4,036.8 | 5,046.0 | 9,082.8 |
| 2040 | 4,036.8 | 10,092.0 | 14,128.8 |

The overall `Total-GPU` summary is still dominated by old FD/VD GPU terms
(for example, about 255,000 GPU node-hours/year from FDs in 2025-2028). So use
the detector-split values above when judging the ND-LAr+TMS scale.

Important caveat after the first trial: if the model's `Events` / `Sim-Events`
are intended to mean ND-LAr events, the TMS-event conversion underestimates
GPU-hours/event by about the TMS/ND-LAr event-rate ratio. Conversely, if the
fields mean TMS reconstructed events, the conversion is internally consistent
but probably not physically tied to the ND-LAr GPU workload.

Best next model shape: keep the primary ND-LAr GPU estimate in POT/spills or
full-spill-equivalent samples, then derive event-equivalent rates only for
display/debugging. If an event-based field has to remain for compatibility,
rename or document whether it means ND-LAr active events, TMS reconstructed
events, spills, or full-spill-equivalent units.

## POT-Based Script

Added `gpu_pot_model.py` as a clean replacement path for ND-LAr/TMS GPU
projection. It keeps full-spill POT as the primary model axis and uses the
existing annual event counts only as a 2025-relative scaling proxy:

```bash
../myenv/bin/python gpu_pot_model.py --outdir gpu_pot_model_output_2025pot2e18_T
```

The script:

- reads annual `Events` or `Sim-Events` from the existing JSON;
- converts those counts into a scale factor relative to the baseline year;
- assigns the baseline year a full-spill POT value;
- applies a full-spill GPU-node-hour cost per 1e18 POT;
- lets other samples enter as relative work factors against nominal full-spill
  production.

Default sample factors are:

- `nominal_full_spill = 1.0`
- `nue_singles = 0.002 / 122`
- `nue_overlay = 1.0`
- `systematic_full_spill = 1.0`

Current conservative/observed-accounting trial:

- baseline year: 2025
- baseline full-spill POT: 2e18
- full-spill GPU cost: 17,992.1 GPU node-hours / 1e18 POT
  - from Nov 2025 + Dec 2025 + Jan 2026 m3249 raw Perlmutter GPU node-hours:
    1,139.7 + 11,351.9 + 5,500.5
- output: `gpu_pot_model_output_2025pot2e18_T/`

Selected current outputs:

| Year | Scale vs 2025 | Full-spill POT (1e18) | GPU node-hours |
| --- | ---: | ---: | ---: |
| 2025 | 1 | 2 | 35,984.2 |
| 2026 | 5 | 10 | 179,921.0 |
| 2030 | 45 | 90 | 1,619,289.0 |
| 2040 | 60 | 120 | 2,159,052.0 |

Older trial outputs, kept for comparison:

- `gpu_pot_model_output_benchmark/`: uses the benchmark rate of
  122 GPU node-hours / 1e18 POT.
- `gpu_pot_model_output_observed21k/`: uses an observed-accounting scale of
  21,000 GPU node-hours / 1e18 POT.
