# NERSC usage analysis

Tooling for turning NERSC IRIS usage exports into numbers the computing model
can use. Companion to `usage/`, which does the same job for fifemon.

## Getting the data

IRIS portal (<https://iris.nersc.gov>) → Reports → usage report → export CSV.
Pull **daily** and **monthly** for each project; daily is what makes production
campaigns visible, monthly is easier to eyeball.

Projects that matter:

| project | what's in it |
|---|---|
| `m3249` | DUNE production. ~99.9% the `dunepro` pseudo-user. |
| `dune`  | General allocation. Individual users — analysis and ML/reco R&D. |

Drop the CSVs in `data/`. Any name matching `nersc_*report*.csv` is picked up;
the tool keys off file contents, not names, so new projects and new allocation
years need no code change.

**The allocation year ends in late January.** An export named `..._2025.csv`
that stops around 2026-01-21 is a *complete* AY2025 record, not a truncated
pull. Usage spikes in the last weeks are often quota burn-down rather than a
coherent production sample — treat them with suspicion when calibrating.

## Running it

```bash
python nersc_usage.py                      # coverage, totals, monthly, prod-vs-analysis
python nersc_usage.py --blocks m3249 --gap 1 --since 2025-11-01
python nersc_usage.py --calibrate 17982 --pot 4e19
```

`--blocks` prints a daily GPU/CPU profile and groups active days into
production blocks. `--threshold` (node-hr/day to count as active, default 50)
and `--gap` (inactive days bridged within a block, default 3) control the
grouping. For the Nov 2025 – Jan 2026 campaign, `--gap 1` separates the
December and January blocks; the default merges them.

`--calibrate` turns a block's node-hours plus the POT it covered into a
per-spill rate suitable for the model's `Reco-*-GPU` fields.

## Units — three easy mistakes

1. **Node-hours are not GPU-hours.** A Perlmutter GPU node is 4x A100, so
   literal GPU-hours = node-hours x 4. IRIS reports node-hours throughout.
2. **A firework is not a spill.** GENIE generation in the ND MiniProd samples
   uses 1e14 POT per firework; a nominal spill is 7.5e13 POT. So
   **1 firework = 1.333 spills**.
3. **Charged is not raw.** They agree in these exports except January 2026
   (4,790 charged vs 5,501 raw). Prefer *raw* for capacity planning — it's the
   machine time actually consumed.

## Slurm job accounting — what IRIS cannot tell you

IRIS aggregates by user / project / host / date. It has no notion of which
production *step* consumed the time. Slurm job accounting does, because the
job names encode the stage.

Pull it with [`sacct_pull.sh`](sacct_pull.sh), run on a Perlmutter login node,
then gzip the results into `data/`:

```bash
./sacct_pull.sh 2025-01-01 2026-10-01 30
gzip -9 sacct_m3249.txt sacct_dune.txt
```

Three things will silently return nothing if you get them wrong, and the
script handles all three — worth knowing if you ever query by hand:

1. **`-a`.** Without it sacct reports only *your own* jobs, so a query for a
   production account comes back empty with no error.
2. **`m3249_g`.** Perlmutter GPU allocations are separate Slurm accounts with
   a `_g` suffix. Querying only `m3249` misses every GPU job.
3. **Chunking.** Wide date ranges fail on this cluster. 30-day chunks work.

Analyse with [`sacct_jobs.py`](sacct_jobs.py):

```bash
python sacct_jobs.py --project m3249 --window 2025-11-01 2026-02-28
python sacct_jobs.py --project m3249 --names
```

It breaks node-hours down by workflow stage and month, and `--window` prints a
per-spill calibration for the production component alone. Node-hours are
`NNodes x Elapsed`, exact for exclusive-node partitions and an overestimate on
`shared_*` ones (which matters for `dune`, not for `m3249`).

**Retention is finite.** The current dump starts 2025-08-26 regardless of the
requested start date — earlier records have aged out. Pull again periodically
or the 2025 campaign becomes unreconstructable.

**What job names do and don't resolve.** They cleanly separate fireworks
production (`fw_gpu` / `fw_cpu`) from Spine ML training (`Spn*`, `SpTr*`),
larnd-sim, and rock generation (`GenRock`) — that distinction matters, because
training is 15.5% of GPU usage and does not scale with POT. They do *not*
identify which MiniProd a production job belongs to: the framework submits
everything under one generic name. That mapping needs production bookkeeping
(justIN / POMS), not NERSC accounting.

## Findings

See [`../model-2025/ND-GPU-CALIBRATION.md`](../model-2025/ND-GPU-CALIBRATION.md)
for what these logs say about the model's ND-LAr GPU parameters, with
provenance for each number.
