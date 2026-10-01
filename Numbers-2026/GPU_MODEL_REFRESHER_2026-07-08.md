# DUNE GPU Model Refresher

This is the "why did we get these numbers?" note for the current ND-LAr/TMS
GPU model pass.

## Where Things Are

Working directory:

`~/.openclaw/shared/computing_model/CCB-data/Numbers-2026/`

Main notes:

- `GPU_MODEL_NOTES.md`
- `gpu_pot_model.py`
- `gpu_pot_model_output_2025pot2e18_T/summary.md`

The project was moved out of the old archive path into:

`~/.openclaw/shared/computing_model/`

## The Problem With The Old Model

The existing JSON model had ND-LAr+TMS GPU inputs like:

- `Reco-Data-GPU = 0.76`
- `Sim-GPU = 4.6`

The old script treated these as GPU-hours per modeled event. That made the
ND-LAr+TMS GPU projection enormous and hard to justify, because "event" is not
a stable unit for this workload.

The key reasoning:

- GPU reconstruction/simulation cost is tied to full-spill detector context.
- A spill contains pileup and multiple interactions.
- TMS reconstructed event counts and ND-LAr event counts are not the same.
- Jeff estimated TMS events are about 2-3x the ND-LAr event rate.
- Many rock muons do not correspond to meaningful reconstruction compute.

So the model should not be driven by literal neutrino interaction counts or a
generic "event" denominator.

## Better Model Axis

The current replacement script treats full-spill POT as the primary axis.

It still reads the old annual `Sim-Events` values, but only to get a relative
year-by-year scale compared with 2025. It does not treat those event counts as
physical output.

Current rule:

`annual full-spill POT = 2025 full-spill POT * annual scale vs 2025`

Then:

`GPU node-hours = full-spill POT in 1e18 units * GPU node-hours per 1e18 POT`

## Current Normalization

For the latest trial we used:

- Baseline year: 2025
- Baseline full-spill POT: `2e18`
- Full-spill GPU cost: `17,992.1 GPU node-hours / 1e18 POT`

That `17,992.1` number came from the m3249 Perlmutter GPU production months
that roughly cover the campaign:

```text
Nov 2025:  1,139.7
Dec 2025: 11,351.9
Jan 2026:  5,500.5
Total:    17,992.1 GPU node-hours
```

Important unit: NERSC reports Perlmutter GPU node-hours. One Perlmutter GPU
node has four A100 GPUs. So:

`literal GPU-hours = GPU node-hours * 4`

## Current Annual Scaling

The old `Sim-Events` values are being used only as relative scale factors.
Relative to 2025, the relevant factors are:

```text
2025:  1x
2026:  5x
2027: 10x
2028: 20x
2029: 30x
2030: 45x
2031+: 60x
```

Since 2025 is assigned `2e18 POT`, this implies:

```text
2025:   2e18 POT
2026:  10e18 POT
2030:  90e18 POT
2040: 120e18 POT
```

This is not claiming we know those POT values are realistic. It is just the
current way of translating the old event-growth curve into a POT-growth curve.

## Main Output Numbers

Using the current assumptions:

```text
2025:    35,984 GPU node-hours
2026:   179,921 GPU node-hours
2030: 1,619,289 GPU node-hours
2040: 2,159,052 GPU node-hours
```

For 2030:

```text
90 * 17,992.1 = 1,619,289 GPU node-hours
```

To convert annual GPU node-hours into continuous capacity:

```text
1,619,289 / 8760 = 184.9 Perlmutter GPU nodes for one full year
```

Since each Perlmutter GPU node has 4 A100s:

```text
184.9 * 4 = 739.6 individual A100 GPUs for one full year
```

So if someone says "2030 needs about 185 GPUs," be careful: that is about 185
Perlmutter GPU nodes, or about 740 literal A100 GPUs.

## What Is Still Uncertain

The current model is intentionally a sanity-check model, not a final estimate.

Things Jeff wants to ask people about:

- Is `2e18 POT` a reasonable 2025 baseline for the production campaign?
- Is `17,992.1 GPU node-hours / 1e18 POT` the right observed-accounting cost?
- Should we use charged or raw node-hours consistently?
- Is the old annual event-growth curve a reasonable proxy for full-spill POT
  growth?
- How much of future production will be nominal full-spill, overlay,
  nu-on-e singles, systematics, retries, or commissioning/debugging?
- What GPU capacity is actually realistic to request or reserve?

The model may be directionally right that DUNE needs a lot of GPU, but the next
step is social/operational: talk to production/NERSC/ND-LAr people and decide
which normalization and future scale are defensible.
