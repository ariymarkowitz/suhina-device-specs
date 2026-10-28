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
    (`reference/dump-12.4.6.json`; the MIDI effects in `reference/dump-midi-12.4.6.json`):
    ranges, defaults, step lists, display text, tapers.
  - **[als 12.4.6]** read from a set saved by Live 12.4.6 (`reference/populate-12.4.6.als`; the
    MIDI effects in `reference/populate-midi-12.4.6.als`): element names and stored values.
  - **[measured 12.4.6]** measured from audio rendered by Live 12.4.6 (`tools/` › 2).
  - **[measured 12.4.7]** measured from audio rendered by Live 12.4.7 (the third set onward). The remaining set was exported after Live's update to 12.4.7 although its sections say 12.4.6; see Measurement sets below.

## Layout

| Path | What |
|---|---|
| [`live-12/audio-effects/`](live-12/audio-effects/) | one note per audio effect of Live 12 (manual chapter 29), file `29.NN-name.md` |
| [`live-12/audio-effects/_template.md`](live-12/audio-effects/_template.md) | the structure every note follows |
| [`live-12/audio-effects/common.md`](live-12/audio-effects/common.md) | controls and behaviour many devices share (side-chain, LFO sync, dry/wet, Hi-Q, the device title bar) |
| [`live-12/audio-effects/INDEX.md`](live-12/audio-effects/INDEX.md) | every device, its family and how complete its note is |
| [`live-12/automation.md`](live-12/automation.md) | how Live plays automation, for every parameter: segments even in the control's position, the Bezier curve family, the volume fader's taper, the smoothing of jumps |
| [`live-12/midi-effects/`](live-12/midi-effects/) | one note per MIDI effect of Live 12 (manual chapter 30), file `30.NN-name.md`, with its own `_template.md`, `common.md` and [`INDEX.md`](live-12/midi-effects/INDEX.md) |
| [`devices/`](devices/README.md) | one folder per device, named like its note (`29.01-amp/`, and `30.01-arpeggiator/` for the MIDI effects): the `runs.py` that defines its measurement runs, the `cases/` file of each run (every case's settings), and `results/`, Live's measured response to each case |
| [`compare/`](compare/README.md) | listen to a Live device and the Suhina device side by side: builds a set that runs a sample through a device's cases, and a page that switches between the two renders |
| [`probes/`](probes/README.md) | the test signals every run plays through the device (44.1 kHz WAV and manifest each), for measuring Live and for rendering a Suhina device the same way |
| [`reference/`](reference/README.md) | what was read from Live 12.4.6 itself: the parameter dump, a readable summary per device, the saved sets that show how Live stores parameters, and the map from API parameters to stored elements |
| [`automation/`](automation/README.md) | the automation runs: hand-made sets, their analyses and `analyse.py` |
| [`tools/`](tools/README.md) | the Suhina Probe device and the measurement harness (`tools/harness/measure.py`) |
| [`AGENTS.md`](AGENTS.md) | notes for coding agents: driving Live through the AbletonMCP Remote Script, what still needs Live's window, how to build a device from a note |
| [`LICENSE`](LICENSE) | the MIT licence, which covers the whole repository |

The probe signals are in [`probes/`](probes/README.md): the exact WAVs (and manifests) the measurements played, so
the same files can be played through a Suhina device for a side-by-side comparison.

Not in the repository, because each can be made again on any machine: the measurement sets
(`work/sets/`, built from the runs by `measure.py build`), and Live's renders of them
(`devices/<device>/renders/`, about 16 MB per case) with the CSV views and impulse responses
written beside the results (`devices/<device>/extras/`). What is kept is what a device is built
from: `results/`.

## Measuring a device yourself

Everything in `devices/<device>/results/` can be measured again, on a machine with
Live 12 and Python 3 (a different Live version gives its own results; compare them with the kept
ones). The only step done by hand is Live's File > Export.

```bash
python3 -m venv tools/.venv && tools/.venv/bin/pip install -r tools/harness/requirements.txt
PY=tools/.venv/bin/python
$PY tools/harness/measure.py list                     # the devices, their runs, their results so far
$PY tools/harness/measure.py build amp                # work/sets/amp/amp.als, and what to export
```

Open `work/sets/amp/amp.als` in Live (a double click, or `live_check.py open` once the Remote
Script is installed, `tools/README.md` › 2b), export every track as `build` prints (a WAV per
track into `work/sets/amp/export/`), then:

```bash
$PY tools/harness/measure.py analyse amp              # results/ and renders/ of devices/29.01-amp/
$PY tools/harness/measure.py summary amp              # the key figures per case
```

`build` and `analyse` take any number of devices (`build amp compressor`, or none for all of
them) and `--run` to pick runs. [`tools/README.md`](tools/README.md) has the details, the export
settings and how to compare a device implementation with these results.

## How a note is used

1. Read the note's **Controls** and **Behaviour** to design the device's parameters (for each:
   id, range, default, unit, taper, steps).
2. Run the **Measurement plan** against Live (render test signals through the device, save a
   Live Set and read the values from the `.als`) to fill the `[measure]` gaps.
3. Write the spec, implement the device and its `.als` import from the note's **Implementation
   notes**, then render the same cases through it and compare with Live's renders
   ([`tools/`](tools/README.md) › 3). How closely to match the note, and what to favour over
   exactness, is in [`AGENTS.md`](AGENTS.md) › Building a device from a note.

## Measurement sets

The runs in `devices/*/runs.py` were measured in batches, and the notes' Measured sections are
headed by the batch ("Third set", "Fifth set"). Each result file in `devices/<device>/results/` is
from the latest batch that has its run.

| Set | Live | Runs | What it did |
|---|---|---|---|
| Compressor and Reverb first runs | 12.4.6 | 2 devices | built by hand with the Suhina Probe's Build cases (the Reverb with 5 sets, `devices/29.32-reverb/README.md`); the other devices were measured from generated sets |
| Top 100 | 12.4.6 | 100 runs, 37 devices | the priority 1 runs: static curves, filter shapes, times, mix laws |
| Remaining | **12.4.7** | 157 runs, 42 devices | priority 2 and 3 runs. It was rendered after Live's update (2026-10-24, 16:17) although its notes say `[measured 12.4.6]`; where a 12.4.6 and a 12.4.7 render of the same settings could be compared they agree (Resonators' default echo, Overdrive and Saturator curves at 1 kHz) and no sound change between the versions was found |
| Third (with a pilot) | 12.4.7 | 147 runs, 39 devices | what the first sets could not move: stored elements (routing, modes, oversampling), automation lanes, MIDI and side-chain key tracks, the extended probe's signals, time behaviour of modulation, fades and glides |
| Fourth | 12.4.7 | 8 runs | candidates the third set left open |
| Fifth | 12.4.7 | 16 runs, 12 devices | everything still open after the fourth, with the fifth probe (Looper, Delay, Filter Delay, Glue Compressor, Limiter, Corpus, Vocoder, Spectral Resonator and Time, Shifter, Roar, Pedal) |
| Reverb network | 12.4.7 | 2 runs | `reverb-network-id` and `reverb-network-scale`: the Reverb's bare tail network at Size 100, Diffusion 0.1 %, filters off, reflections at their minimum |

Everything tagged `[measured 12.4.7]` was rendered by Live 12.4.7. The sets above were built,
opened in Live, checked with `live_check.py verify` (every case matched, except the few listed under
Quirks in `tools/README.md`), exported at 44.1 kHz and analysed, and each answer was written into the
note. The figures the notes quote often need more than `analyse.py` gives (Hilbert envelopes, lag
matching, spectra of a window, offline models of a clipper or resampler for aliasing); the notes say
how each was read, and the one-off scripts are not kept. The MIDI effects were recorded in one
Arrangement take (`tools/harness/midi_set.py`) and the automation runs are in `automation/`.

## State and open points

All 42 audio effects of Live 12's chapter 29 and the eight MIDI effects of chapter 30 have a note
with a Measured section (INDEX: `partly measured`; Compressor's measurements are in its Behaviour
section). Ranges, defaults, step lists, display units and tapers are `[dump 12.4.6]`
(`reference/dump-12.4.6.json`, `reference/dump-midi-12.4.6.json`), the `.als` names and stored
values `[als 12.4.6]`. Automation playback is in [`live-12/automation.md`](live-12/automation.md)
and Utility's note.

What the notes still list as open (each is in its note's Measurement plan or Measured section):

- **Looper:** the partner of the end-of-loop fade, the fade at the start of a recording, Reverse on
  layered loops, whether the write low-pass scales with the sample rate, Undo and other states.
- **Delay and Filter Delay:** the crossfade length in Delay's Fade, and Hi-Quality off or Eco on a ramp.
- **Glue Compressor:** the oversampling's delay in samples, and at 48 kHz.
- **Corpus:** why only the default Tune is exact, the ends of LFO Rate, sync step 17 against its
  listed value, Duty Cycle, the sign of the Phase and Offset shifts.
- **Vocoder:** the rule at 200 to 800 Hz and at the Upper limit, and the tracker's latency.
- **Spectral Resonator:** the grain envelope and Pitch Mod 2 and 4 st in each mode.
- **Shifter:** Width; Spin does nothing in Live 12.4.7 (probably a bug there).
- **Roar:** Feedback Amount and the filter Morph again (Morph in the middle, Feedback Amount at 50 %),
  Blend in a two-stage routing, cells below 1, negative cells, other stages' targets.
- **Pedal:** Gain 25 and 75 %, 10 dB steps at 20 Hz and 5 kHz.
- **Not reachable from audio with static settings:** MIDI pitch bend and velocity, Hybrid Reverb's
  impulse choice, automation beyond `automation/`.
