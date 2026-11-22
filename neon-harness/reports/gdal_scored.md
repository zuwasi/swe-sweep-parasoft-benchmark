# GDAL — Neon bug-hunt vs SWE-Sweep bugs (scored)

Denominator: all 72 SWE-Sweep bugs, including the 4 empty-region bugs (2ca07c262bf8, 8a4bee4f8d2a,
cefd3547d91a, d8a8cd51d51b, not matchable).

## Accepted

- **GDAL-034** (High) — "32-bit signed overflow in `iPrime` indexes `anPrimes[-10..-1]` on >2G-pixel
  integer rasters (OOB read & potential SIGFPE)" (alg/gdalchecksum.cpp 72, 208-224).
  Bug `gdal-af647aafa367` ("nXSize*2 int overflow", MEMORY; oracle hunks in alg/gdalchecksum.cpp at
  100/206/251, blob cc631881bf).
  Maintainer fix: commit 08f382ae4c "GDALChecksumImage(): fix 3.6.0 regression regarding integer overflow
  on images with more than 2 billion pixels (fixes #8254)". The fix rewrites the three overflow sites with
  size_t/int64 casts, including the exact `iPrime = (nValsPerIter * (iY * nXSize + iXStart)) % 11;`
  expression inside GDAL-034's cited span (208-224), whose signed overflow produces the negative iPrime
  and the anPrimes[-10..-1] OOB read the finding describes. Same defect family (int overflow on >2G-pixel
  rasters), same lines. **ACCEPT region + strict.**

## Clear misses

The remaining 71 bugs had no Neon finding whose spans reached their regions (matcher output). The 4
empty-region bugs are not matchable.

## Final score

| Metric | Neon | Parasoft (published) |
|---|---|---|
| Region | 1/72 = 1.4% | 4.2% |
| Strict | 1/72 = 1.4% | 1.4% |

Novel findings: Neon reported 116 findings across the repo; 115 did not correspond to a SWE-Sweep bug.
Not vetted for real-vs-false; counted as unmatched.
