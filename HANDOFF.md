# Handoff — ND-LAr GPU calibration

Jeff Kleykamp, postdoc ending 2026-10-02. This branch (`jkleyka_Sep2026`, off
`kherner_Oct2025`) holds an unfinished effort to replace the ND-LAr+TMS GPU
parameters in the computing model with values grounded in measured NERSC usage.

If you are picking this up cold, read this file, then
[`model-2025/ND-GPU-CALIBRATION.md`](model-2025/ND-GPU-CALIBRATION.md). Those
two are the whole story.

## Why this work exists

The model projects ND-LAr GPU needs by multiplying a per-event GPU rate by an
annual event count. Both halves turned out to be unreliable:

- `Reco-Data-GPU = 0.76` GPU-hr/event is a 2023 estimate made before real GPU
  workflows existed. It has never been renormalised.
- `Reco-Sim-GPU = 0.0222` carries a JSON comment citing NERSC node-hours, but
  those numbers are not in NERSC accounting — they come from the ND Resource
  Projections benchmark document.
- "Event" is not defined anywhere, and for the ND it could mean at least five
  different things that differ by orders of magnitude.

Left alone, the model produces ND-LAr GPU projections in the millions of node
hours per year against measured usage of tens of thousands.

## The one decision that blocks everything

**Does an ND "event" in the timeline CSV mean a spill?**

The evidence says yes: ND-SAND and ND-LAr+TMS carry identical event counts
(impossible for per-detector interaction counts), and `15e6 events/yr x 7.5e13
POT/spill = 1.125e21 POT/yr`, which is DUNE nominal beam. But it is
undocumented, and nobody has confirmed it.

Everything downstream depends on this. It is a short conversation with the
ND-LAr production people, not a research task. Do it first.

If the answer is "spill", the measured rate is **0.135–0.27 GPU-hr/spill** and
the calibration is nearly done. If the answer is "interaction", the whole
per-event framing needs rethinking, because GPU cost attaches to the spill — a
per-interaction rate is only valid at one pileup level.

## State

Done:

- NERSC IRIS exports for allocation year 2025 are in `nersc/data/`, with a
  reusable analysis tool (`nersc/nersc_usage.py`). New exports drop in and run
  with no code changes.
- The campaign is characterised: Nov 2025 – Jan 2026, 17,982 raw GPU
  node-hours, two blocks, both reconstruction rather than generation.
- The provenance of every GPU/CPU number currently in the JSON is traced.
- `model-2025/2025-12-10.py` — the checked-in `2025-10-26.py` points at a stale
  config, and plain `nbconvert` leaves an IPython magic that crashes outside
  Jupyter. This is the working converted script.

Not done, deliberately:

- **No JSON values have been changed.** Changing them before the unit question
  is settled would relabel the confusion rather than fix it. The numbers in
  the JSON are known-wrong; the notes say by how much and in which direction.
- `Analysis-GPU` is declared in the JSON but never computed — the driver's
  analysis block loops over `["CPU"]` only. Measured analysis GPU is 1.73x
  production GPU, so this is the larger of the two categories and the model
  books zero for it. Fixing it is a one-line change plus a ratio nobody has
  chosen.

## What I would do first

1. Settle the unit question (above).
2. Pull an IRIS export for allocation year 2026 into `nersc/data/` and run
   `python nersc/nersc_usage.py --blocks m3249 --gap 1 --since 2026-01-22`.
   That gives MiniProd 5.3 as an independent second calibration point. The
   AY2025 rate rests on a single campaign whose POT coverage is uncertain by a
   factor of two.
3. Run the `sacct` query in `nersc/README.md` to map GPU blocks onto named
   production steps. IRIS cannot do this; Slurm job names usually can. This is
   the cheapest way to resolve the factor of two.
4. Then, and only then, edit the JSON.

## Who knows what

- **Ken Herner** — author of `kherner_Oct2025` and of the current
  `Reco-Sim-GPU` / `Reco-Sim-CPU` values. Worth asking directly where 8,900
  GPU node-hours and 18,600 CPU node-hours came from, and what sample the
  "1.6M events" denominator refers to. Nothing else reconciles with that number.
- **ND-LAr production** — owns the MiniProd campaigns, and can answer both the
  unit question and which POT the Dec/Jan GPU work actually processed.
- **Heidi Schellman / Mike Kirby** — original authors of the model and its
  per-event structure.

## Traps

- **Windows checkouts of this repo fail.**
  `Numbers-2023/external/Countries----Sum-Wallclock-Time-(cores-*-months)-...csv`
  contains a `*`, which NTFS forbids, and it aborts checkout of every branch.
  Fix: `git config core.protectNTFS false`, then a no-cone sparse-checkout
  with `/*` plus a `!` negation for that path.
- **Node-hours are not GPU-hours.** A Perlmutter GPU node is 4x A100. Silent 4x.
- **A firework is not a spill.** 1e14 vs 7.5e13 POT. Silent 1.33x.
- **NERSC allocation years end in late January.** An export ending 2026-01-21
  is complete, not truncated, and the spike before it is quota burn-down rather
  than a coherent production sample.
