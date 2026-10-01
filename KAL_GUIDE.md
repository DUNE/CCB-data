# Kal guide: CCB-data computing model (focus: ND-LAr+TMS)

This repo is a snapshot of the **DUNE computing resource model** and some helper tooling used for **CCB** (computing board) style resource projections.

There are two mostly-separate tracks inside the repo:

1) **Projection model** ("what we will need")
2) **Usage summaries** ("what happened", extracted from fifemon)

Since you said you want a **projection** (out to ~2040), the most relevant area is `Numbers-2024/`.

---

## Top-level layout

- `README.md`
  - High-level description and the intended "how to run" workflow.
  - Mentions that the "current" version is on a particular upstream branch (e.g. `CCB-Jun24`) and that this directory contains older snapshots.

- `Numbers-2022/`, `Numbers-2023/`, `Numbers-2024/`
  - The **projection model** at different moments in time.
  - `Numbers-2024/` is the most relevant for the DOE23/NDLAr-era model.

- `usage/`
  - Scripts + cached outputs for building **usage summaries** from fifemon CSV exports.
  - Not required for doing a projection, but useful for sanity-checking.

- `fifemon/`
  - Small helper tables like `sites.csv`, `nations.csv` used for labeling/mapping.

- `data/`
  - Misc input spreadsheets/CSVs used historically for accounting / storage breakdowns.

- `strip.py`, `clean.sh`
  - Housekeeping helpers (strip/clean up files for sharing/committing). (I haven’t audited every detail; treat as repo hygiene utilities.)

---

## Projection model: `Numbers-2024/`

### What you *edit*
For new projections, you normally:

1) Copy a JSON parameter file (don’t overwrite the original)
2) Point a notebook at your copied JSON
3) Re-run the notebook to regenerate plots/tables

The JSON is where the “physics/processing assumptions” live.

**Key JSONs currently present:**

- `DOE23-NDLAr_2023-11-03-2040.json`
  - A DOE23-style model that includes an `ND-LAr+TMS` detector block.

- `CCB_Prep_2023-12-11-2040.json`
  - A CCB-prep variant that includes additional detector categories (e.g. `2x2`, `LBL`, `HighE`, `LowE`, `Calib`).
  - If you only care about ND-LAr+TMS and want fewer moving parts, the DOE23-NDLAr JSON is often simpler.

There are also `*_internal.json` files. These typically include more detail/notes and/or intermediate state used in the original authors’ workflow. I generally treat them as:
- useful reference
- not the cleanest starting point for a new “public” scenario

### What you *run*
The main “engine” is a Jupyter notebook.

Notebooks present:
- `2023-11-03.ipynb` (big; likely the main/latest-ish notebook for the DOE23-NDLAr era)
- `2023-12-12-HMS.ipynb` (another big notebook, likely a later variant)
- `2023-07-03.ipynb` (older)

The notebooks depend on:
- `NumberUtils.py`
  - plotting helpers (`DrawDet`, `DrawType`)
  - CSV emitters (`ToCSV1`, `ToCSV2`)
  - cumulative/retention logic (`cumulateMap`, `extendMap`)

### What comes out
When you run the notebook, it typically writes:
- plots (`*.png`)
- tables (`*.csv`)
- and sometimes small LaTeX snippets (`*.tex`) that embed the plots/tables

You’ll see examples of “output directories” that match a scenario name, e.g.:
- `CCB_Prep_2023-12-11-2040_noMWC/`
- `DOE23-NDLAr_2023-11-03-2040_noMWC/`

Those are basically **rendered outputs for a particular scenario**.

---

## The model inputs (what matters for ND-LAr+TMS)

Inside a parameter JSON (e.g. `DOE23-NDLAr_2023-11-03-2040.json`), inputs break down into:

### 1) Global axes / bookkeeping
- `Years`: explicit list of years (2018…2040)
- `Detectors`, `CombinedDetectors`: which detector blocks exist and how they’re grouped
- `MinYear`, `MaxYear`: plotting range
- `Units`, `Formats`: labels/printing

### 2) Per-detector block parameters (where “new bigger sims” usually feed in)
For `ND-LAr+TMS` specifically, the block includes:

Per-event storage:
- `Raw-Store` (MB/event)
- `Reco-Data-Store` (MB/event)
- `Sim-Store` (MB/event)

Per-event compute:
- `Reco-Data-CPU` (CPU hours per event)
- `Sim-CPU` (CPU hours per event)
- optionally GPU:
  - `Reco-Data-GPU` (GPU hours per event)
  - `Sim-GPU` (GPU hours per event)

Memory assumptions (affects the “memory-weighted” CPU/core conversion):
- `Reco-Memory` (MB)
- `Sim-Memory` (MB)

Event counts (year-by-year; huge impact):
- `Events`: data events per year (in “millions” in these JSONs)
- `Test`: commissioning/test volumes (comments say TB)
- `Sim-Events`: simulated events per year (millions)

Analysis scaling:
- `Analysis-CPU`: ratio of analysis CPU relative to reco+sim CPU (often 0.5)

### 3) Retention / copies / reprocessing policy (turns yearly rates into cumulative disk/tape)
These are global knobs:
- `DiskLifetimes`, `TapeLifetimes` (years)
- `DiskCopies`, `TapeCopies` (replication factors)
- `Reprocess` (how many years back a “new pass” reprocesses)
- `PerYear` (how many times per year various passes happen)
- `AnalysisExtend` (analysis continues N years after the last reco/sim)

### 4) “CCB responsibility splits” (optional, but used for CCB-style plots)
- `SplitsYear`, `SplitsEarly`, `SplitsLater`
  - how FNAL/CERN/National responsibilities are divided for disk/tape/CPU.

---

## Usage summaries: `usage/` (optional for your current goal)

Even though you said not to worry about usage right now, here’s what’s there so you know what you’re ignoring:

- `usage/monthly.py`
  - Parses a manually-downloaded fifemon CSV export of **monthly** slot hours.
  - Outputs a bunch of tables under `usage/output/` (by site and by country), in units like `kHS23-Yrs`.

- `usage/daily.py`
  - Same idea, but can be run in a daily or monthly mode (there’s a `scale = "monthly"` toggle inside).
  - Uses the fifemon export’s categories to split into:
    - Production (Owner:dunepro)
    - MARS (Jobsub_SubGroup:mars)
    - Analysis (everything else)
    - Total
    - plus derived `NoMARS`

- `usage/output/`
  - Cached CSV tables already generated (e.g. `Total_BySite_kHS23-Yrs_...csv`).

- `usage/pix/`
  - Heatmap-style PNG plots of the usage tables.

---

## Suggested workflow for *your* ND-LAr+TMS projection update

1) Pick a starting scenario JSON
   - Usually `Numbers-2024/DOE23-NDLAr_2023-11-03-2040.json` is a decent baseline for ND-LAr+TMS.

2) Copy it to a new name (so your scenario is explicit)
   - Example: `DOE23-NDLAr_2026-02-11-2040_Jeff.json`

3) Update the `ND-LAr+TMS` block
   - Update per-event costs/sizes from your latest benchmarks (larger sims)
   - Update yearly `Sim-Events` (and possibly `Events`) according to the new campaign plan

4) Open the notebook and point it at your new JSON
   - One of `2023-11-03.ipynb` or `2023-12-12-HMS.ipynb` should already contain logic for reading one of these JSONs.

5) Run the notebook cells; collect outputs
   - Plots/tables should appear either in the working directory or in a subdirectory named after the JSON/scenario.

---

## Notes / gotchas

- The model uses a **memory-weighted** CPU concept (“MWC”). So updating `Reco-Memory` / `Sim-Memory` can materially change the effective CPU/core numbers.

- ND-LAr+TMS in the JSON has comments indicating the sim CPU estimate includes factors like:
  - scaling up for data stats
  - adding rock sim
  - doubling for systematic samples
  If your “larger sims” already include some of these effects, you’ll want to avoid double-counting.

---

If you want, tell me which notebook you plan to use (`2023-11-03.ipynb` vs `2023-12-12-HMS.ipynb`) and I’ll add a short "where to change the JSON filename inside the notebook" note once I peek at the relevant cell(s).
