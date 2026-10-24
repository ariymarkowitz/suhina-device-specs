# Remaining priority 1 to 3 runs (Live 12.4.6), in one set

The 157 runs of the devices' `runs.py` files that the top 100 (`../top100/`) did not take: 25 of
priority 1, 100 of priority 2 and 32 of priority 3. `selection.json` lists them, priority first.

State: **built, opened in Live, verified, exported and analysed; the answers are not yet written
into the device notes.**

- Export: two renders of selected tracks, 44.1 kHz WAV 32-bit, Normalize off: tracks 1 to 926
  (2 s probe) as `remaining` at 24 bars, the last 41 (10 s probe) as `remaining-gap10` at 60 bars,
  967 files, 16 GB, into `export/` (not in the repository). Live named one file
  `remaining autopan-attack attack-0.5-1.wav`; it was renamed to `... attack-0.5.wav`.
- `batch.py analyse --trim`: offset 0 samples from all 44 bypass renders; 967 renders analysed
  into the devices' `live/` (`remaining.analysis.json`). 54 cases have no impulse in the render
  (closed gates, Beat Repeat idling, Volume 0, Amp Volume 0 and the like); none is silent
  throughout.

- `batch.py build measurements/remaining/selection.json`: 1134 cases on 967 tracks (151 runs on
  the 2 s probe, 6 on the 10 s probe). `remaining.als`, `remaining.cases.json`.
- `live_check.py verify`: 1133 of 1134 cases match (`remaining.verified.json`). The other,
  `shifter-envelope default`, sets Env Amount to 0 st: stored as asked, and Live reads API 0.5
  where the harness took 0.46875, the other end of the flat 0.00 st stretch of the display.
- Two harness faults showed up while building and were fixed (`tools/harness/make_als.py`, with
  tests): a display at the very end of a control's range (Delay Feedback 95 %) was refused as
  outside it by a float32 rounding, and five parameters whose display is a tapered curve (Redux
  Jitter, Roar Feedback, Auto Filter LFO Amount, Chorus Warmth, Hybrid Reverb Algo Delay) were
  mapped as storing the API value when the element stores the displayed number. Before the fix
  Algo Delay 100 ms came out as 501 ms. `measurements/als-map-12.4.6.json` has the five corrected.

Next: read the runs (`batch.py summary measurements/remaining/selection.json [run ...]`) and
write each answer into its device note, as for the top 100.
