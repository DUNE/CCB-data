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

From `nersc/data/` (IRIS, project m3249, `dunepro`, perlmutter gpu, raw
node-hours). The Nov 2025 – Jan 2026 campaign:

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

| POT denominator | GPU node-hr / 1e18 POT | GPU-hr / spill |
|---|---|---|
| 4e19 — nominal + nu-on-e overlay, per the ND Resource Projections doc | 450 | **0.135** |
| 2.77e19 — MiniProd 5.1 + 5.2 as configured | 649 | **0.195** |
| 2e19 — MiniProd 5.1 + 5.2 nominal | 899 | **0.270** |

So the defensible current statement is **0.135–0.27 GPU-hr/spill**. Compare the
JSON's `Reco-Data-GPU = 0.76` (2.8–5.6x too high) and `Reco-Sim-GPU = 0.0222`
(6–12x too low).

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
4. **Which step ran when?** IRIS cannot say. Needs `sacct` job names; see
   [`../nersc/README.md`](../nersc/README.md).
5. **Where did the upstream run?** 6,367 CPU node-hours for the whole year
   cannot have generated 2.77e19 POT of GENIE + edep-sim at any plausible rate,
   so it ran on the grid, and NERSC accounting will never show it.
6. **What fraction of analysis GPU should the model budget**, and as a ratio to
   what?

## 7. Next data to pull

An IRIS export covering 2026-01-22 onward — the new allocation year. That
brings in MiniProd 5.3 and whatever followed, giving a second independent
campaign to calibrate against. Earlier years would also help establish a trend.
Drop new exports into `../nersc/data/` and re-run; no code changes needed.
