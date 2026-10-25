# Suhina resources

Working notes for building [Suhina's](https://github.com/suhina-daw/suhina-daw) own built-in effects and instruments from scratch, matching
the controls and behaviour of the devices Live 12 ships with, so that a Live Set's devices can
import into Suhina devices that look, respond and sound as close as possible.

The notes assume no existing implementation: each describes what Live's device does, how it is
stored in a Live Set and how to measure what is still unknown, so a device can be designed,
built and checked from its note alone. They are the step *before* a spec: when a device is about
to be built, its note is checked, measured, and the parts that hold up are written into the
implementation's own specification.

## For coding agents building a device

If you are an LLM agent implementing a Suhina device from one of these notes, possibly working
from another checkout such as suhina-daw, read
[`AGENTS.md`](https://github.com/ariymarkowitz/suhina-device-specs/blob/main/AGENTS.md) ›
Building a device from a note before you start. In short:

- Quality and performance come first: an algorithm in the same class as Live's, clean output at
  every sample rate, and under 1 % of one core per instance. Accuracy and simplicity come second.
- Log every trade-off in the spec's Decisions list, and every measurement outside `compare.py`'s
  tolerances in its Known differences.
- Ranges, defaults, tapers and steps (`[dump]`, `[als]`) are exact. Treat `[inferred]` and
  `[source: N]` facts as guesses to check against the renders.
- The clean-room rules below carry over: write the spec in your own words, and name Live only
  where suhina-daw's `AGENTS.md` allows it.

## Clean-room rules for these notes

- Knowledge comes only from public documentation (the Live 12 Reference Manual, Ableton's help
  centre and blog), published reviews and articles, community observations and measurements, and
  our own observation of the running program. **Never** from disassembled or decompiled Ableton
  binaries, decompiled remote scripts or leaked code.
- Everything is written in our own words. No copied sentences from the manual or any other
  source, no copied tables, no screenshots. Control names, value ranges, units and defaults are
  facts and are recorded as such.
- Every fact carries a confidence tag and, where it came from elsewhere, a source:
  - **[manual]** stated in the Live 12 Reference Manual (chapter 29, or 30 for the MIDI effects).
  - **[source: N]** from an external source listed at the bottom of the note.
  - **[inferred]** follows from the manual or general DSP practice but is not stated anywhere.
  - **[measure]** unknown; the note says how to measure it.
  - **[dump 12.4.6]** read from Live 12.4.6 through the Live API by the Suhina Probe
    (`measurements/dump-12.4.6.json`; the MIDI effects in `measurements/dump-midi-12.4.6.json`):
    ranges, defaults, step lists, display text, tapers.
  - **[als 12.4.6]** read from a set saved by Live 12.4.6 (`measurements/populate-12.4.6.als`; the
    MIDI effects in `measurements/populate-midi-12.4.6.als`): element names and stored values.
  - **[measured 12.4.6]** measured from audio rendered by Live 12.4.6 (`tools/` › 2).
  - **[measured 12.4.7]** measured from audio rendered by Live 12.4.7 (the third set, `measurements/third/`). The remaining set was exported after Live's update to 12.4.7 although its sections say 12.4.6; see `measurements/third/README.md` › Live 12.4.7 against the `[measured 12.4.6]` tags.

## Layout

| Path | What |
|---|---|
| [`live-12/audio-effects/`](live-12/audio-effects/) | one note per audio effect of Live 12 (manual chapter 29), file `29.NN-name.md` |
| [`live-12/audio-effects/_template.md`](live-12/audio-effects/_template.md) | the structure every note follows |
| [`live-12/audio-effects/common.md`](live-12/audio-effects/common.md) | controls and behaviour many devices share (side-chain, LFO sync, dry/wet, Hi-Q, the device title bar) |
| [`live-12/audio-effects/INDEX.md`](live-12/audio-effects/INDEX.md) | every device, its family and how complete its note is |
| [`live-12/automation.md`](live-12/automation.md) | how Live plays automation, for every parameter: segments even in the control's position, the Bezier curve family, the volume fader's taper, the smoothing of jumps |
| [`live-12/midi-effects/`](live-12/midi-effects/) | one note per MIDI effect of Live 12 (manual chapter 30), file `30.NN-name.md`, with its own `_template.md`, `common.md` and [`INDEX.md`](live-12/midi-effects/INDEX.md) |
| [`tools/`](tools/README.md) | the Suhina Probe device and the measurement harness |
| [`AGENTS.md`](AGENTS.md) | notes for coding agents: driving Live through the AbletonMCP Remote Script, what still needs Live's window |
| [`LICENSE`](LICENSE) | the MIT licence, which covers the whole repository |
| `measurements/` | what the tools produced from Live 12.4.6: the dump (and a readable summary per device in `dump-12.4.6-summary/`), the saved sets, the probe signal's manifest (`probe.json`), and the map from API parameters to stored set elements for calibrated devices (`als-map-12.4.6.json`, `tools/README.md` › 2b) |
| [`measurements/automation/`](measurements/automation/README.md) | the automation runs: hand-made sets, their analyses and `analyse.py` (renders not in the repository) |
| `measurements/29.NN-name/` | one folder per device, named like its note, for its behaviour runs: each run's cases file (`<run>.json`), `<run>.built.json` and saved set (`<run>.als`) at the top, Live's renders in `export/` (not in the repository) and their analyses in `live/` |

The large audio files are not in the repository: the probe signal (`probe.wav`, about 16 MB) and
Live's renders (each device's `export/`, about 16 MB per case). Comparing an implementation only
needs the analyses in each device's `live/`. To recreate the probe signal, run
`tools/.venv/bin/python tools/harness/signals.py -o measurements/probe.wav --rate 44100 --gap 2`
(the noise is seeded, so it matches the original). Live's renders can only be recreated by
running the measurement again in Live (`tools/README.md` › 2).

## How a note is used

1. Read the note's **Controls** and **Behaviour** to design the device's parameters (for each:
   id, range, default, unit, taper, steps).
2. Run the **Measurement plan** against Live (render test signals through the device, save a
   Live Set and read the values from the `.als`) to fill the `[measure]` gaps.
3. Write the spec, implement the device and its `.als` import from the note's **Implementation
   notes**, then render the same cases through it and compare with Live's renders
   ([`tools/`](tools/README.md) › 3). How closely to match the note, and what to favour over
   exactness, is in [`AGENTS.md`](AGENTS.md) › Building a device from a note.

## State and next steps (2026-10-25)

All 42 audio effects of Live 12's chapter 29 have a note. The Suhina Probe has been built in Live
12.4.6 (`tools/probe-device/Suhina Probe.amxd`) and its parameter dump is in the notes: ranges,
defaults, step lists, display units and tapers are tagged `[dump 12.4.6]`, and the `.als`
element and parameter names `[als 12.4.6]`. Behaviour (curves, times, filter shapes) is measured
by behaviour runs ([`tools/`](tools/README.md) › 2 and 2b): the first (Compressor Threshold) is in
`tools/README.md` › First run in Live 12.4.6, the Reverb's in `measurements/29.32-reverb/`, the
top 100 runs of 37 devices in one set in [`measurements/top100/`](measurements/top100/README.md),
and the other 157 priority 1 to 3 runs of all 42 devices in a second set in
[`measurements/remaining/`](measurements/remaining/README.md), whose answers are written into the
notes. A third set of 147 runs on 39 devices (1048 renders, five parts and a pilot) was rendered in
Live 12.4.7 ([`measurements/third/`](measurements/third/README.md)) and read into the notes as
`[measured 12.4.7]` (Measured › Third set). All 42 notes now have a Measured section with
`[measured 12.4.6]` facts (INDEX: `partly measured`; Compressor's are in its Behaviour section).

The eight MIDI effects of chapter 30 have notes too ([`live-12/midi-effects/`](live-12/midi-effects/INDEX.md)),
dump checked from their own dump (`measurements/dump-midi-12.4.6.json`); all eight have a
Measured section from one recording of the devices' MIDI output (`measurements/midi-effects/`,
`tools/harness/midi_set.py`); (the shared plan is in that folder's `common.md`).

Automation playback is measured from seven hand-made sets (`measurements/automation/`): how a
segment moves, the curve family, the volume fader's taper and the smoothing of jumps are in
[`live-12/automation.md`](live-12/automation.md), and Utility's Gain taper and smoothing in its note.

Next: the eight candidate runs added to the devices' `runs.py` files after the third set (listed in
[`measurements/third/README.md`](measurements/third/README.md) › Settings that did not read, and what is
open: Compressor's 50 Hz buzz with the side-chain EQ off, Delay's time jumps with noise, the
Phaser-Flanger envelope times, Spectral Resonator's Mod Rate and frequency dial, Spectral Time's
processing order, the Vocoder's band counts and Pitch Tracking limits), the other open points the notes
list (every other candidate in the devices' `runs.py` files has been run), and what audio with static
settings cannot show (MIDI pitch bend and velocity, Roar's other matrix cells, Shifter's Spread;
automation beyond the parameters in `measurements/automation/`).

## Licence

Everything in this repository, code, notes and measurement data, is under the MIT licence
([`LICENSE`](LICENSE)). Ableton, Live and Max are trademarks of their owners, and this project is
not affiliated with them.
