# ND-LAr GPU calibration — status, provenance, open questions

Working notes for replacing the ND-LAr+TMS GPU parameters in
`NearTerm_*.json` with numbers grounded in measured NERSC usage rather than
2023-era estimates. Analysis tooling and the raw exports are in
[`../nersc/`](../nersc/).

Nothing in the JSON has been changed yet. The unit question below should
settle first, or a new number just relabels the existing confusion.

## 1. The unit problem

"Per event" is not well defined for the ND. At least five different things
could be meant, and they differ by orders of magnitude:

- a **spill** (full readout window, with pileup and rock muons)
- an **ND-LAr fiducial neutrino interaction** (tens per spill)
- a **single-interaction event** (simulated in isolation — no pileup, no rock)
- a **TMS reconstructed event**
- a **SAND event**

GPU cost attaches to the *spill*, because the ML reco runs on the whole
detector image. Dividing by interactions gives a rate that is only valid at one
pileup level.

**The timeline CSV already appears to use spills.** Two pieces of evidence:

```
ND-SAND      Raw-Events   2032+: 15 Million
ND-LAr+TMS   Raw-Events   2032+: 15 Million     <- identical
ND-SAND      Sim-Events   2025: 1   2026: 1.6
ND-LAr+TMS   Sim-Events   2025: 1   2026: 1.6   <- also identical
```

SAND and ND-LAr have very different masses and interaction rates, so identical
counts cannot be per-detector interactions. And `15e6 x 7.5e13 POT/spill =
1.125e21 POT/year`, which is DUNE nominal beam. The numbers only work if an ND
"event" is a beam pulse.

This is undocumented, which is why the field reads as ambiguous. Making it
explicit is the single highest-value change to the config.

### The exceptions that break it

- **nu-on-e singles** are not spills. 2e22 POT for roughly 40 node-hours in the
  Nov–Jan campaign. On a per-POT axis they look enormous and cost nothing; they
  need their own line or should be dropped as a rounding error. The nu-on-e
  *overlay* samples are genuine full spills and do cost full rates.
- **Pre-2025 sim samples were single-interaction** — no pileup, no rock. So the
  `Sim-Events` column means something different before and after 2025, and no
  single rate is correct across it. The historical actuals therefore cannot
  validate the forward projection. Fixing this needs either the pre-2025
  entries re-expressed in spill-equivalents or a separate DataType; the driver
  hardcodes the `Raw-Events→Reco-Data` / `Sim-Events→Reco-Sim` pairs, so a new
  sample type means editing that loop.

## 2. Measured GPU

Two independent sources, and they agree: IRIS usage reports and Slurm job
accounting reconcile to **99.94%** month by month on m3249 Perlmutter GPU
(59,155 vs 59,192 node-hours over Sep 2025 – Oct 2026). The only visible
discrepancies are January and February 2026, +837 and −950, which cancel —
sacct attributes a job to the month it *started*, IRIS to the day the time was
*used*, so month-spanning jobs shift between them.

### What the job names show

Slurm job names resolve the workflow stage, which IRIS cannot. Of 59,155 GPU
node-hours on m3249:

| stage | node-hours | share |
|---|---:|---:|
| `fw_*` fireworks production | 45,446 | 76.8% |
| `Spn*` / `SpTr*` Spine ML training | 9,183 | 15.5% |
| larnd-sim / segmentation | 2,166 | 3.7% |
| interactive, misc, other | 2,360 | 4.0% |

**Spine ML training is 15.5% of GPU usage and does not scale with POT.** It is
model development, not production. Any per-spill rate must exclude it. The
February 2026 burst that looks like a huge campaign is about two-thirds
production and one-third training.

Production GPU and production CPU are also almost disjoint in time:

```
          fw_gpu    fw_cpu
2025-12   11,110         5
2026-01   11,760         0
2026-02   17,008         2     <- GPU-only reconstruction phase
2026-05    1,715     4,226
2026-06      282     2,763     <- CPU-heavy phase, probably a later generation
2026-07        3     2,064
```

Two named jobs settle a question that was open: `MiniProdN5p1_NDComplex_FHC`
and `MiniProdN5p2_NDComplex_RHC` confirm **MiniProd 5.1 = FHC, 5.2 = RHC**, so
5.1 + 5.2 are the "FHC nominal + RHC nominal" 2e19 in the ND Resource
Projections doc. What the names do *not* resolve is which MiniProd each
`fw_gpu.slurm.sh` job belongs to — the fireworks framework submits everything
under that one generic name, and the explicitly-named MiniProd jobs are a
handful of hand-submitted conversion steps totalling under 200 node-hours.

### The campaign

Reproduce with `python ../nersc/sacct_jobs.py --project m3249 --window
2025-11-01 2026-02-28`.

**Fireworks production, Nov 2025 – Feb 2026: 40,569 GPU node-hours** (against
20 CPU node-hours — this phase is purely reconstruction).

| POT denominator | GPU node-hr / 1e18 POT | GPU-hr / spill |
|---|---:|---:|
| 4e19 — nominal + nu-on-e overlay | 1,014 | **0.304** |
| 2.77e19 — MiniProd 5.1 + 5.2 as configured | 1,465 | **0.439** |
| 2e19 — MiniProd 5.1 + 5.2 nominal | 2,028 | **0.609** |

So **0.30–0.61 GPU-hr/spill**, production only.

**This supersedes an earlier figure of 0.135–0.27 in this file.** That was
computed from 17,982 node-hours, which was all m3249 GPU activity within
allocation year 2025 only. It undercounted on two sides: the campaign
continued past the 2026-01-21 allocation boundary into February (2.26x more
production compute), and it included training and interactive time that should
have been excluded.

The consequence matters: **`Reco-Data-GPU = 0.76` now sits only 1.25x above the
high end of the measured range**, rather than the 5.6x too high that the
earlier figure implied. If an ND "event" means a spill, the original 2023
estimate is approximately right, and the thing that was badly wrong is
`Reco-Sim-GPU = 0.0222`, which is 14–27x too low.

### Earlier IRIS-only view, kept for reference

From IRIS alone (project m3249, `dunepro`, perlmutter gpu, raw node-hours),
before the stage breakdown was available:

```
Nov 01–30      ramp / testing  GPU  1,134   CPU  603
Dec 01–10      GPU idle        GPU     20   CPU  177
Dec 11–Jan 03  block           GPU 11,807   CPU  500   sustained 600–800/day
Jan 04–06      gap             GPU     15   CPU   58
Jan 07–21      block           GPU  5,005   CPU  125   bursty
                               ──────────────────────
campaign total                 GPU 17,982   CPU 1,464
```

Reproduce with `python ../nersc/nersc_usage.py --blocks m3249 --gap 1
--since 2025-11-01`.

Both blocks have negligible CPU, so both are reconstruction rather than
generation. The record ends 2026-01-21 because the NERSC allocation year ends
there — this is a complete AY2025 record, and the January block is at least
partly end-of-year quota burn-down rather than a coherent sample.

**The rate depends on which POT the campaign covered, and that is not settled:**

Dividing that 17,982 by the same POT denominators gave 450 / 649 / 899 node-hr
per 1e18 POT, i.e. 0.135 / 0.195 / 0.270 GPU-hr per spill — the superseded
range. It is recorded here only so that the figure is recognisable if it turns
up in a slide or an email from this period. Use the production-only numbers
above.

## 3. MiniProd arithmetic

GENIE generation uses 1e14 POT per firework; a nominal spill is 7.5e13 POT, so
**1 firework = 1.333 spills**. Treating them as interchangeable is a 33% error.

| | fireworks | POT configured | spills |
|---|---|---|---|
| MiniProd 5.1 | 149,148 | 1.492e19 | 198,864 |
| MiniProd 5.2 | 128,000 | 1.280e19 | 170,667 |
| combined | 277,148 | 2.772e19 | 369,531 |

5.1 = 64,000 x 2 configs (SAND drift, SAND STT) + 10,574 x 2 additional.
5.2 = 64,000 x 2, no additional jobs recorded.

Both are quoted as "1e19 POT (1.28e19 genie fireworks configured)". That 1.28x
gap between configured and nominal is unexplained and scales any derived rate
by 28% depending on which is the right denominator.

## 4. Provenance of the numbers currently in the JSON

| value | comment in JSON | actually from |
|---|---|---|
| `Reco-Sim-GPU = 0.0222` | "8900 NSERC GPU node hours x 4 A100 / 1.6M events" | **Not these logs.** 8,900 is about half the measured 17,982. |
| `Reco-Sim-CPU = 2.97` | "18600 NSERC CPU node hours x 256 threads / 1.6M events" | **Not these logs.** Total m3249 CPU for the entire allocation year is 6,367 node-hours. |
| `Reco-Data-GPU = 0.76` | — | 2023 estimate, never renormalised. |

The 18,600 / 8,900 pair is close to Table 2 of the ND Resource Projections
document (CPU 20,460 / GPU 9,800), so these are benchmark projections, not
NERSC measurements, despite the comments naming NERSC.

The `1.6M events` denominator is unverified and matches nothing else: not
533,333 campaign spills, not 369,531 MiniProd spills, and not an interaction
count at any stated pileup. Any rate derived by dividing by it inherits that.

## 5. Also missing: analysis GPU

| AY2025, raw node-hours | |
|---|---|
| production (`dunepro`/`dunepr`, both projects) | 22,088 |
| individual users (`dune` project) | 38,211 |
| **analysis : production** | **1.73** |

Analysis GPU is larger than production GPU, and the model computes **zero** for
it. `Analysis-GPU` is declared in `Scales` and `PerYear` but the driver's
analysis block loops over `["CPU"]` only, so the series is never created.

Caveat: that 1.73 is all-DUNE, dominated by ML/reco R&D users, not ND-LAr
specific.

## 6. Open questions

1. **Which POT did the Nov–Jan campaign actually cover?** Worth a factor of 2
   on the headline rate. Everything else is secondary to this.
2. **How many events did each MiniProd produce?** Not needed if the ND event
   stays a spill — but it is the check on whether it should. `events / 533,333
   spills` landing near the expected interactions-per-spill would confirm the
   interaction reading; landing near 3 means the count means something else.
3. **Configured vs nominal POT** — which is the right denominator (28%).
4. ~~Which step ran when?~~ **Answered** by the sacct pull — production,
   training and generation now separate cleanly. What remains unresolved is
   *which MiniProd* a given production job belongs to: the fireworks framework
   submits everything as `fw_gpu.slurm.sh` / `fw_cpu.slurm.sh`, so the names
   identify the stage but not the campaign. Splitting 5.1 from 5.2 from 5.3
   needs the production bookkeeping (justIN / POMS), not NERSC accounting.
5. **Where did the upstream run?** Partly answered. `fw_cpu` totals 13,089
   node-hours across Aug 2025 – Sep 2026, most of it Mar–Jul 2026, i.e. after
   the GPU reconstruction phase rather than before it. That is still far too
   little to have generated 2.77e19 POT of GENIE + edep-sim, so the bulk ran on
   the grid and NERSC accounting will never show it. It is also now the closest
   measured counterpart to the 18,600 CPU node-hours cited in the JSON, within
   about 1.4x — close enough to be worth asking Ken Herner whether that is what
   the number referred to.
6. **What fraction of analysis GPU should the model budget**, and as a ratio to
   what?
7. **Should Spine ML training be modelled at all?** It is 15.5% of production
   GPU and does not scale with POT, so it cannot be folded into a per-spill
   rate — but it is real, recurring usage that someone has to pay for. It
   probably belongs as a separate flat line rather than a per-event term.

## 7. Next data to pull

Both the AY2026 IRIS export and the Slurm job accounting are already in
`../nersc/data/`. What is still missing:

- **Production bookkeeping** (justIN / POMS, or the production team's own
  campaign records) to map `fw_gpu` jobs onto named MiniProds and to get the
  POT each one covered. This is the remaining factor of two on the rate, and
  NERSC data cannot supply it.
- **A later IRIS and sacct pull.** Slurm retention starts 2025-08-26 in the
  current dump, so anything earlier has aged out — pull again before that
  window closes on the 2025 campaign.

Drop new exports into `../nersc/data/` and re-run; no code changes needed.
Both plain and gzipped files are read.
