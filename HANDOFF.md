# Handoff — ND-LAr GPU calibration

Jeff Kleykamp, postdoc, ended 2026-10-04. Successor: Daniel.

This branch (`jkleyka_Sep2026`, off `kherner_Oct2025`) holds an unfinished
effort to put the ND-LAr+TMS GPU numbers in the DUNE computing model on a
measured footing instead of a 2023 guess.

**Read in this order:**

1. This file — what the work is and where it stands.
2. [`GETTING-STARTED.md`](GETTING-STARTED.md) — how to set up, run the model,
   and pull fresh data off NERSC.
3. [`model-2025/ND-GPU-CALIBRATION.md`](model-2025/ND-GPU-CALIBRATION.md) —
   the technical detail, with provenance for every number.

---

## What this project is

DUNE has to tell its funding agencies how much computing it will need for the
next fifteen years. The **CCB** (Computing Contributions Board) is where the
collaborating countries agree who supplies what. This repository holds the
model that produces those projections — CPU, GPU, disk and tape by detector,
by year, out to 2040 — and the usage summaries used to sanity-check them.

The model is simple in structure. For each detector you give it:

- how many **events** per year (in a timeline CSV), and
- how much each event **costs** — CPU-hours, GPU-hours, TB of storage (in a
  JSON config).

Multiply, apply retention and replication policies, aggregate, plot. That's it.
The difficulty is entirely in whether those two inputs are right.

**ND-LAr** is DUNE's near detector liquid-argon TPC. It matters here because
its reconstruction uses machine learning on GPUs, which is new, expensive, and
was never calibrated against anything real.

---

## Where things stood, and why

The model projected ND-LAr GPU needs in the **millions** of node-hours per
year. Measured usage is **tens of thousands**. That gap is what this work was
chasing.

Two causes, and only one of them turned out to be real:

**The rates were never checked.** `Reco-Data-GPU = 0.76` GPU-hr/event is a 2023
estimate made before any real GPU workflow existed. `Reco-Sim-GPU = 0.0222`
carries a comment citing NERSC node-hours that do not appear anywhere in NERSC
accounting — they are benchmark projections from a planning document.

**The unit is undefined — this is the real problem.** For the ND, "event"
could mean a spill, an ND-LAr neutrino interaction, a TMS reconstructed event,
or a SAND event. Those differ by **orders of magnitude**: a spill contains
roughly 30–100 ND-LAr interactions depending on who you ask. Nothing in the
repository says which is meant.

### What was measured

Pulling the real NERSC logs (both IRIS accounting and Slurm job records, which
agree with each other to 99.94%) gives, for fireworks production over
Nov 2025 – Feb 2026:

> **0.30–0.61 GPU-hr per spill**

The factor-of-two spread is which POT that campaign covered, which NERSC data
cannot resolve.

**The surprise: `Reco-Data-GPU = 0.76` sits only ~1.25x above the high end.**
If an ND "event" means a spill, the original 2023 estimate was roughly right
all along. The number that is badly wrong is `Reco-Sim-GPU = 0.0222`, which is
**14–27x too low**.

So the headline is not "the model is wildly overestimating GPU." It is "the
model's units were never written down, and one of two rates is badly off."

---

## The one decision that blocks everything

> **Does an ND "event" in the timeline CSV mean a spill?**

The arithmetic says yes:

- ND-SAND and ND-LAr+TMS carry **identical** event counts in the timeline.
  They have very different masses and interaction rates, so identical counts
  cannot be per-detector interactions.
- `15e6 events/yr x 7.5e13 POT/spill = 1.125e21 POT/yr`, which is DUNE nominal
  beam exposure. That is not a coincidence.

But nobody has confirmed it, and everything downstream depends on it. **This is
a short conversation with the ND-LAr production people, not a research task.**
Do it before touching any number.

If the answer is "spill", the calibration is nearly finished — fix
`Reco-Sim-GPU`, document the unit, done. If it is "interaction", the per-event
framing itself needs rethinking, because GPU cost attaches to the whole spill
image, so a per-interaction rate is only valid at one pileup level.

---

## State

**Done:**

- NERSC IRIS exports for allocation years 2025 and 2026, plus Slurm job
  accounting, all in `nersc/data/`, with reusable analysis tools. New exports
  drop in and run with no code changes.
- The Nov 2025 – Feb 2026 campaign characterised: 40,569 GPU node-hours of
  fireworks production, cleanly separated from 9,183 node-hours of Spine ML
  **training**, which is 15.5% of GPU usage and does *not* scale with beam.
  Any per-spill rate must exclude training.
- Provenance traced for every GPU and CPU number currently in the JSON.
- `model-2025/2025-12-10.py` — a working driver script. The checked-in
  `2025-10-26.py` points at a stale config and will silently give you the wrong
  answer; use the 12-10 one.

**Deliberately not done:**

- **No JSON values were changed.** The config now carries a loud comment block
  marking the GPU numbers as known-wrong, with the measured range — but the
  values themselves are untouched, because changing them before the unit
  question is settled would relabel the ambiguity rather than fix it. A
  half-corrected config nobody can explain is worse than an uncorrected one
  with honest notes.
- **`Analysis-GPU` is declared but never computed.** The driver's analysis
  block loops over `["CPU"]` only, so the series is never created. Measured
  analysis GPU is **1.73x production GPU**, so the model books zero for the
  larger of the two categories. The code fix is one line; choosing the ratio is
  a judgement call that needed someone with more context than a departing
  postdoc.

---

## What I would do, in order

1. **Settle the unit question.** Free, unblocks everything.
2. **Get the production bookkeeping** (justIN / POMS, or ask the production
   team) to find out how much POT the Nov 2025 – Feb 2026 campaign covered, and
   which MiniProd each production job belonged to. This is the remaining factor
   of two. NERSC data cannot supply it — the fireworks framework submits
   everything under one generic job name.
3. **Re-pull NERSC data periodically.** Slurm accounting retention is finite;
   the current dump already starts 2025-08-26 regardless of what was requested.
   See `GETTING-STARTED.md`.
4. **Then** fix `Reco-Sim-GPU`, document the unit in the JSON, and decide what
   to do about analysis GPU and ML training.

---

## Who to ask

- **Ken Herner** — wrote the `kherner_Oct2025` branch and the current
  `Reco-Sim-GPU` / `Reco-Sim-CPU` values. Worth asking directly: where did
  8,900 GPU and 18,600 CPU node-hours come from, and what does the "1.6M
  events" denominator refer to? Nothing measurable matches that number. (The
  closest real figure is 13,089 `fw_cpu` node-hours, within ~1.4x of 18,600 —
  possibly what it meant.)
- **ND-LAr production** — owns the MiniProd campaigns. Can answer the unit
  question and the campaign-POT question, which are the two that matter.
- **Heidi Schellman, Mike Kirby** — original authors of the model and its
  per-event structure.

---

## Traps

Each of these is silent — wrong answers, no error message.

- **Windows checkouts of this repo fail.**
  `Numbers-2023/external/Countries----Sum-Wallclock-Time-(cores-*-months)-...csv`
  contains a `*`, which NTFS forbids, and it aborts the checkout of *every*
  branch. Fix in `GETTING-STARTED.md`.
- **Node-hours are not GPU-hours.** A Perlmutter GPU node holds 4 A100s.
  Silent 4x.
- **A firework is not a spill.** GENIE generation uses 1e14 POT per firework;
  a spill is 7.5e13 POT. Silent 1.33x.
- **GPU allocations are separate Slurm accounts** with a `_g` suffix. Querying
  `m3249` instead of `m3249_g` silently returns no GPU jobs at all.
- **`sacct` shows only your own jobs** unless you pass `-a`. A query for a
  production account returns nothing, with no error.
- **NERSC allocation years end in late January.** An export named `..._2025`
  ending 2026-01-21 is complete, not truncated — but work continued into the
  next allocation year, and missing that undercounted the campaign by 2.26x.
  It is the mistake that produced an earlier, wrong answer of 0.135–0.27
  GPU-hr/spill, which you may still see in slides from this period.
- **Charged node-hours are not raw node-hours.** There is a 50% discount when
  certain criteria are met, so charged understates actual machine use by up to
  ~1.9x in some months. Use **raw** for capacity planning.
