# Top 100 behaviour runs (Live 12.4.6), in one set

State (2026-10-18, second session): **built, opened, verified, exported and analysed; the device
notes are not updated yet** (next steps 4 and 5). Branch `top100-measurements` (not pushed).

## Done in the second session

- `live_check.py open`: 690 tracks in 30 s. `verify`: 802 of 805 cases match
  (`top100.verified.json`). The other 3 are Limiter Ceiling/Threshold at −12 dB: stored as
  −12 dB as asked, but Live's API value is 0.1882 where the harness predicted 0.1719. The display
  has two significant digits, so a run of API values reads "−12 dB" and the harness took the low
  end of it; 0.1882 lies between the dump's −14 dB at 0.125 and −10 dB at 0.25, as −12 dB should.
- **Every clip was Sample Offline** at first (`The file "probe.wav" could not be opened` in Live's
  `Log.txt`): Live 12.4.6 loads no sample of a set that is not in a Project folder, whatever the
  clip's Path says, and the earlier calibration sets had the same problem unnoticed (verify reads
  only devices). `make_als.py` now writes an empty `Ableton Project Info/` beside every set.
- Export: All Individual Tracks, 1.1.1, 60 bars, WAV 32-bit 44.1 kHz, Normalize off, name
  `top100`, into `export/`; 691 files (690 tracks and the Main), 27 GB, 11 GB after `--trim`.
  Live writes a "/" in a track name as "_" in the file name (two tracks); `batch.py` follows that.
- `batch.py analyse --trim`: offset 0 samples from all 36 gap2 and 3 gap10 bypass renders; 690
  renders analysed into the devices' `live/` (`top100.analysis.json`). `summary` runs.
- Silent renders: `utility-gain gain--inf` (expected), `amp-gain gain-0` (Amp gives nothing at
  Input Gain 0) and `beatrepeat-gate gate-1-16` (Gate = Grid: nothing repeats); the last two are
  findings for the notes, not render faults.

## What is here

- `selection.json`: the 100 runs, the set name (`top100`) and the two probes. Every run is a
  priority-1 candidate (see below) except 25 left out to make 100.
- `top100.als`: one Live Set, **690 tracks for 805 cases**. Each run's `bypass`, and any case
  that two runs share, plays on one track (`make_als.py build --share`). Tracks are ordered by
  probe: the gap2 tracks first, then the gap10 tracks (32 tracks: Hybrid Reverb algorithms and decay,
  Resonators decay, Spectral Resonator decay). Every clip points at one of the two shared probe
  files (`../probe.wav`, `../29.32-reverb/probe-gap10/probe.wav`); nothing is copied.
- `top100.cases.json`: per case, its track, probe, and each parameter's API and stored value.
- Each run's cases file is written beside its device's `runs.py` (`measurements/29.NN-*/<run>.json`).

The candidates: three Sonnet agents read every note's Measurement plan and wrote
`measurements/29.NN-*/runs.py` for all 42 devices: 257 runs, priority 1 (125), 2 (100) and 3 (32),
each with `question`, `plan` step, `read` (which analysis answers it) and `why`. `batch.py check`
passes on all of them. Spectrum, Tuner, Looper and External Audio Effect only have token
priority-3 runs; little about them can be measured from audio with static settings.

## Tooling added in this session

- `tools/harness/batch.py`: `check`, `build`, `analyse`, `summary`; see its docstring.
- `make_als.py build`: `--share` (one track per identical device state and probe) and a
  per-cases-file `"probe"`.
- `live_check.py open <set>`: opens a set (`open -a`) and waits through the Remote Script until it
  is loaded; `verify` follows each case's `track`.
- Tests: `tools/harness/tests/test_batch.py` and new tests in `test_make_als.py`; all 57 pass.
- `AGENTS.md` (repository root): drive Live through the AbletonMCP Remote Script, not its window.
- `tools/README.md` › 2b, `measurements/29.32-reverb/README.md`, `README.md`: pointers to that.
- A trial (`compressor-ratio` alone) was built, opened with `live_check.py open` and passed
  `verify` with 0 problems in Live 12.4.6.

## Next steps

`PY=tools/.venv/bin/python`

1. Done. **Open and verify** (Remote Script, no UI):
   ```bash
   $PY tools/harness/live_check.py open measurements/top100/top100.als --timeout 900
   $PY tools/harness/live_check.py verify measurements/top100/top100.cases.json -o measurements/top100/top100.verified.json
   ```
   690 tracks is far more than any earlier set (37 to 91); if Live struggles, split the selection
   into two selection files and build two sets.
2. Done (all tracks at once). **Export: the one UI step.** Ask the user first whether they will click it or allow control of
   Live (the user declined desktop control once in this session and asked for the MCP route).
   File › Export Audio/Video, WAV, 32-bit, 44.1 kHz, Normalize off, into `measurements/top100/export/`.
   Either: all tracks at once, name `top100`, length 60 bars (the gap10 probe, 118.75 s), then
   `analyse --trim`; that needs about 690 × 42 MB ≈ 29 GB until the trim. Or two exports (less disk):
   select the gap2 tracks, Selected Tracks Only, 24 bars, name `top100`; then the gap10 tracks
   (the last 32), 60 bars, name `top100-gap10`.
3. Done. **Analyse and summarise:**
   ```bash
   $PY tools/harness/batch.py analyse measurements/top100/selection.json --export measurements/top100/export [--trim]
   $PY tools/harness/batch.py summary measurements/top100/selection.json > <scratch>/summary.txt
   ```
   `analyse` takes each probe group's offset from its bypass renders (an export has come out 40 ms
   early before) and writes into each device's `live/`.
4. **Update the device notes** (`live-12/audio-effects/29.NN-*.md`): for each run, the answered
   plan step gets a `[measured 12.4.6]` fact in Controls, Behaviour or a Measured section. Many runs'
   `read` says the renders need a reading `analyse.py` does not do (pitch of the steady tone,
   long FFT of `.ir.wav`, envelopes); do those from the renders. Split this by device group between
   agents, as the candidate step was.
5. **Document and commit**: a findings section here, `tools/README.md` › 2b for `batch.py` and
   `--share`, the INDEX remarks, and `.gitignore` for any large `.ir.wav` sets. Commit when the
   user asks.

## Known points from the candidates

- Roar's routing mode is not an API parameter: every Roar run plays in the loaded mode, and
  `roar-routing-default` finds out what that mode does. If it does not feed stage 1 from the
  input, the other Roar runs show only part of the signal.
- Corpus has two parameters named Width: `Width` is the filter bandwidth, `Width #2` the stereo width.
- Glue Compressor's Ratio, Attack and Release are set by index (no item names in the API).
- Beat Repeat runs use the impulse at bar 1 as the trigger reference.
- Not measurable this way: automation, side-chain, MIDI, Hi-Quality/Oversampling, the Hybrid
  Reverb IR choice, Vocoder carrier and band count, Spectral Time resolution, Utility Mid/Side.
