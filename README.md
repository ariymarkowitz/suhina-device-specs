# Suhina resources

Working notes for building Suhina's own built-in effects and instruments from scratch, matching
the controls and behaviour of the devices Live 12 ships with, so that a Live Set's devices can
import into Suhina devices that look, respond and sound as close as possible.

The notes assume no existing implementation: each describes what Live's device does, how it is
stored in a Live Set and how to measure what is still unknown, so a device can be designed,
built and checked from its note alone. They are the step *before* a spec: when a device is about
to be built, its note is checked, measured, and the parts that hold up are written into the
implementation's own specification.

## Clean-room rules for these notes

- Knowledge comes only from public documentation (the Live 12 Reference Manual, Ableton's help
  centre and blog), published reviews and articles, community observations and measurements, and
  our own observation of the running program. **Never** from disassembled or decompiled Ableton
  binaries, decompiled remote scripts or leaked code.
- Everything is written in our own words. No copied sentences from the manual or any other
  source, no copied tables, no screenshots. Control names, value ranges, units and defaults are
  facts and are recorded as such.
- Every fact carries a confidence tag and, where it came from elsewhere, a source:
  - **[manual]** stated in the Live 12 Reference Manual (chapter 29).
  - **[source: N]** from an external source listed at the bottom of the note.
  - **[inferred]** follows from the manual or general DSP practice but is not stated anywhere.
  - **[measure]** unknown; the note says how to measure it.
  - **[dump 12.4.6]** read from Live 12.4.6 through the Live API by the Suhina Probe
    (`measurements/dump-12.4.6.json`): ranges, defaults, step lists, display text, tapers.
  - **[als 12.4.6]** read from a set saved by Live 12.4.6 (`measurements/populate-12.4.6.als`):
    element names and stored values.
  - **[measured 12.4.6]** measured from audio rendered by Live 12.4.6 (`tools/` › 2).

## Layout

| Path | What |
|---|---|
| [`live-12/audio-effects/`](live-12/audio-effects/) | one note per audio effect of Live 12 (manual chapter 29), file `29.NN-name.md` |
| [`live-12/audio-effects/_template.md`](live-12/audio-effects/_template.md) | the structure every note follows |
| [`live-12/audio-effects/common.md`](live-12/audio-effects/common.md) | controls and behaviour many devices share (side-chain, LFO sync, dry/wet, Hi-Q, the device title bar) |
| [`live-12/audio-effects/INDEX.md`](live-12/audio-effects/INDEX.md) | every device, its family and how complete its note is |
| [`tools/`](tools/README.md) | the Suhina Probe device and the measurement harness |
| `measurements/` | what the tools produced from Live 12.4.6: the dump (and a readable summary per device in `dump-12.4.6-summary/`), the saved sets, the probe signal, the Compressor run's exports and analyses |

## How a note is used

1. Read the note's **Controls** and **Behaviour** to design the device's parameters (for each:
   id, range, default, unit, taper, steps).
2. Run the **Measurement plan** against Live (render test signals through the device, save a
   Live Set and read the values from the `.als`) to fill the `[measure]` gaps.
3. Write the spec, implement the device and its `.als` import from the note's **Implementation
   notes**, then render the same cases through it and compare with Live's renders
   ([`tools/`](tools/README.md) › 3).

## State and next steps (2026-10-18)

All 42 audio effects of Live 12's chapter 29 have a note. The Suhina Probe has been built in Live
12.4.6 (`tools/probe-device/Suhina Probe.amxd`) and its parameter dump is in the notes: ranges,
defaults, step lists, display units and tapers are tagged `[dump 12.4.6]`, and the `.als`
element and parameter names `[als 12.4.6]`. What remains `[measure]` is behaviour (curves, times,
filter shapes), which the behaviour runs in [`tools/`](tools/README.md) › 2 measure, one device and
parameter at a time. The first such run (Compressor Threshold) and what it showed about the
tooling are in `tools/README.md` › First run in Live 12.4.6.
