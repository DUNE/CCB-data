# Getting started

Practical how-to for this repository: getting it checked out, running the
model, and pulling fresh usage data off NERSC. For *why* any of it matters,
read [`HANDOFF.md`](HANDOFF.md) first.

---

## 1. Clone it (read this before you try, especially on Windows)

```bash
git clone git@github.com:DUNE/CCB-data.git
cd CCB-data
git checkout jkleyka_Sep2026
```

**On Windows this will fail** with:

```
error: invalid path 'Numbers-2023/external/Countries----Sum-Wallclock-Time-(cores-*-months)-by-Site-and-Year-(Custom-VOs)-.csv'
```

One file in the repository has a `*` in its name. NTFS forbids that character,
so the checkout aborts — on *every* branch, not just this one, and it leaves
you with an empty working tree that looks alarming. It is not your fault and
nothing is broken.

Fix it by telling git to skip that one path:

```bash
git config core.protectNTFS false
git sparse-checkout init --no-cone
printf '/*\n!Numbers-2023/external/Countries----Sum-Wallclock-Time-(cores-*-months)-by-Site-and-Year-(Custom-VOs)-.csv\n' > .git/info/sparse-checkout
git checkout jkleyka_Sep2026
```

You get every file except that one, which nothing in the current work uses.
Also worth setting, so Windows permission bits don't show up as spurious
changes:

```bash
git config core.fileMode false
```

On Linux or macOS none of this applies — clone and check out normally.

---

## 2. Python environment

```bash
python -m venv .venv
.venv/Scripts/python -m pip install matplotlib numpy scipy ipykernel commentjson nbconvert
```

(`.venv/bin/python` on Linux/macOS.)

**`dune_plot_style` is not on PyPI.** `pip install dune_plot_style` fails. It
is a DUNE package that must be installed from a local copy — there is one in
the parent directory of this repo as `dune_plot_style-01_02/`, or clone
<https://github.com/DUNE/dune_plot_style>:

```bash
.venv/Scripts/python -m pip install ../dune_plot_style-01_02
```

It installs under the import name `dunestyle`, not `dune_plot_style`. Check:

```bash
.venv/Scripts/python -c "import dunestyle.matplotlib"
```

should print `DUNE plot style enabled`.

A `myenv/` directory exists in the sibling `CCB-data_my_version` clone. It is a
Linux virtualenv with absolute paths baked in and will not work anywhere else.
Ignore it.

**PowerShell note:** `&&` is a syntax error in Windows PowerShell 5.1. Chain
with `;` or run commands one at a time. The examples here are bash.

---

## 3. Run the model

```bash
cd model-2025
../.venv/Scripts/python 2025-12-10.py
```

Takes a few seconds and writes about a hundred plots, CSVs and LaTeX fragments
into `NearTerm_2025-12-10-2030_noMWC/`, plus a full dump in
`NearTerm_2025-12-10-2030_noMWC_results.csv`. Those outputs are gitignored —
they regenerate, so don't commit them.

**Use `2025-12-10.py`, not the checked-in `2025-10-26.py`.** The latter still
hardcodes an older config file, so it runs fine and gives you the wrong model
with no warning.

### How the model is configured

Two files, and the split matters:

| file | holds |
|---|---|
| `NearTerm_2025-12-10-2040.json` | time-**independent**: per-event costs, retention and replication policy, plotting |
| `NearTerm_2025-12-10-2040_timeline.csv` | time-**dependent**: events per year, per detector |

To try a scenario, copy *both*, edit your copies, and change `configfilename`
near the top of the driver script. The JSON names its own timeline file, so
keep them consistent.

The engine is `DataHolder.py`. It indexes every series by a five-part tag —
`Detector!DataType!Resource!Location!Units` — and ends up with roughly 1,500 of
them after all the aggregations. `model-2025/README.md` explains the internal
model; read it before modifying the engine.

### Regenerating the driver from the notebook

The `.py` files are converted from Jupyter notebooks:

```bash
../.venv/Scripts/python -m jupyter nbconvert --to script 2025-12-10.ipynb
```

One manual step afterwards: nbconvert leaves `get_ipython().system(...)` in the
output, which raises `NameError` outside Jupyter. Replace that line with
`json2tex.runit(configfilename, dirname, test=True)`. (The repo's `gitadd.sh`
refers to a `../convert.sh` that stripped these, but that script is not in the
tree.)

---

## 4. Getting data off NERSC

Two different sources, and you need both — they answer different questions.

| source | answers | cannot answer |
|---|---|---|
| **IRIS** usage reports | how many node-hours, by user/project/day | what the time was spent *on* |
| **Slurm** job accounting (`sacct`) | job names, i.e. which workflow stage | — but retention is finite |

They cross-check each other. When last compared they agreed to 99.94%, which is
how you know both are trustworthy.

### Which projects

| project | what's in it |
|---|---|
| `m3249` | DUNE **production**. ~99.9% the `dunepro` pseudo-user. This is the one that matters. |
| `dune` | general allocation — individual users, analysis and ML R&D |
| `m5170` | another small DUNE-related project; negligible (41 GPU node-hours/yr), ignore |

### 4a. IRIS usage reports

Web UI, at <https://iris.nersc.gov> — you need a NERSC account with access to
the project. Find the usage report, and export **CSV**. Pull **four** files:
daily *and* monthly, for `m3249` *and* `dune`. Daily is what makes production
campaigns visible as blocks; monthly is easier to read.

Set the date range to the allocation year you want, or explicitly from the day
after the last pull. Drop the files in `nersc/data/`.

Filenames just need to contain `compute` or match `nersc_*report*`, and end
`.csv` — the tool keys off file *contents*, not names. Matching what's already
there is easiest: `daily_compute_m3249.csv`, `monthly_compute_dune.csv`.

Then:

```bash
python nersc/nersc_usage.py
python nersc/nersc_usage.py --blocks m3249 --gap 1 --since 2025-11-01
```

The second prints a day-by-day GPU/CPU profile and groups busy days into
production blocks.

### 4b. Slurm job accounting

Copy [`nersc/sacct_pull.sh`](nersc/sacct_pull.sh) to a Perlmutter login node
and run it there (`sacct` only exists on the cluster):

```bash
scp nersc/sacct_pull.sh perlmutter.nersc.gov:~/
ssh perlmutter.nersc.gov
chmod +x ~/sacct_pull.sh
~/sacct_pull.sh 2025-01-01 2026-10-01 30
gzip -9 sacct_m3249.txt sacct_dune.txt
```

Copy the `.gz` files back into `nersc/data/`. Then, locally:

```bash
python nersc/sacct_jobs.py --project m3249 --window 2025-11-01 2026-02-28
python nersc/sacct_jobs.py --project m3249 --names
```

Three things make a hand-written `sacct` query return **nothing, with no error
message**. The script handles all three, but you'll hit them if you improvise:

1. **`-a`** — without it, sacct reports only *your own* jobs. A query for a
   production account comes back empty.
2. **`m3249_g`** — Perlmutter GPU allocations are *separate Slurm accounts*
   with a `_g` suffix. Querying only `m3249` misses every GPU job.
3. **Chunking** — wide date ranges fail on this cluster. 30-day chunks work;
   drop to 7 if a chunk returns zero rows with a nonzero return code.

**Retention is finite.** The current dump starts 2025-08-26 no matter what
start date you ask for — everything earlier has aged out. Re-pull periodically
or campaigns become unreconstructable.

### Reading the results

Job names identify the workflow stage:

| name | what it is |
|---|---|
| `fw_gpu.slurm.sh`, `fw_cpu.slurm.sh` | **fireworks production** — the thing you want to calibrate on |
| `Spn*`, `SpTr*` | Spine **ML training** — 15.5% of GPU use, does *not* scale with beam, exclude it |
| `*larnd*`, `SegFFE` | larnd-sim and segmentation |
| `GenRock` | rock muon generation |
| `MiniProdN5p1_*`, `MiniProdN5p2_*` | explicitly named MiniProd steps (5.1 = FHC, 5.2 = RHC) |

What job names **cannot** tell you is which MiniProd a given production job
belongs to — the framework submits everything as `fw_gpu.slurm.sh`. For that
you need the production bookkeeping (justIN / POMS), not NERSC.

### Units, where people go wrong

```
literal GPU-hours = node-hours x 4        (a Perlmutter GPU node is 4x A100)
1 spill           = 7.5e13 POT
1 firework        = 1e14 POT = 1.333 spills
```

Use **Raw Hours**, not **Node Hours Charged**. There is a 50% discount when
certain criteria are met, so charged understates real machine use — by ~1.9x in
some months of AY2026.

---

## 5. Where everything lives

```
CCB-data/
  HANDOFF.md                      <- start here
  GETTING-STARTED.md              <- this file
  model-2025/                     <- the current model
    2025-12-10.py                   the driver to run
    NearTerm_2025-12-10-2040.json   per-event costs and policy
    NearTerm_..._timeline.csv       events per year
    DataHolder.py                   the engine
    ND-GPU-CALIBRATION.md           what the NERSC logs say, with provenance
    README.md                       the internal model, by its author
  nersc/                          <- usage analysis
    nersc_usage.py                  IRIS reports
    sacct_jobs.py                   Slurm job accounting
    sacct_pull.sh                   run this on Perlmutter
    README.md
    data/                           all the exports
  usage/                          <- older fifemon-based usage summaries
  Numbers-2022..2024/             <- superseded model versions, kept for history
```

There is a second clone, `CCB-data_my_version`, on branch
`jkleyka_numbers2026`. Its `Numbers-2026/` directory holds an earlier
POT-based exploration built on the *old* model schema. It is kept for the
reasoning in `GPU_MODEL_NOTES.md`; the code there has two known arithmetic
errors, documented in its commit message, and should not be used as-is.
