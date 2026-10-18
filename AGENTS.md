# Notes for agents working in this repository

Read `README.md` first (clean-room rules, confidence tags) and `tools/README.md` before measuring.

## Talking to Live: use the Remote Script, not the window

Live 12 is driven through the **AbletonMCP Remote Script**, which runs inside Live and answers
JSON commands on `127.0.0.1:9877`. Use it through `tools/harness/live_check.py` (`PY` is
`tools/.venv/bin/python`):

| Task | Command |
|---|---|
| Is Live listening? | `nc -z 127.0.0.1 9877` |
| Open a set and wait until it is loaded | `$PY tools/harness/live_check.py open <set>.als` |
| Read every track's devices and parameter values | `$PY tools/harness/live_check.py read -o <file>.read.json` |
| Check a generated set against what it should hold | `$PY tools/harness/live_check.py verify <set>.cases.json -o <set>.verified.json` |
| Anything else the script offers | `live_check.Live().call("<command>", **params)` in Python |

The script's other commands include `get_session_info`, `get_track_info`, `get_device_parameters`,
`set_device_parameter`, `set_tempo`, `start_playback`/`stop_playback`, `get_arrangement_clips`
and browser access (`grep command_type` in
`~/Music/Ableton/User Library/Remote Scripts/AbletonMCP/__init__.py` lists them all).

- **Do not install or start the `ableton-mcp` project's MCP server.** Only its Remote Script is
  installed: the server can record sessions to a remote dataset. Talk to the socket directly, as
  `live_check.py` does.
- **Make sets as files, not by hand.** `make_als.py build` (one or a few runs) and `batch.py build`
  (many devices' runs in one set) write the measurement set; `live_check.py open` loads it and
  `verify` checks it. Do not use the Suhina Probe's Build cases button, drag files in, or change a
  measurement set through `set_device_parameter`: a set has to be reproducible from its cases files.
- If port 9877 is not listening, ask the user to start Live with AbletonMCP chosen as a Control
  Surface (`tools/README.md` › 2b). Do not fall back to clicking through Live instead.

## What still needs Live's window

Live's API has no audio export, and the Remote Script cannot arm, route or record tracks. So
**File › Export Audio/Video** is the one step that needs the UI. Settings are in
`tools/README.md` › 2, step 5: All Individual Tracks (or Selected Tracks Only), the probe's
length in bars, WAV, 32-bit, Normalize off, into the batch's `export/` folder, under the export
name the batch expects. Before taking control of Live's window, ask the user. They may prefer to
click the export themselves from the exact settings you give them. Settings dialogs, installing
the Suhina Probe and Max editing are also UI-only and the user's to do.

## Measuring and tests

- New behaviour runs go in a device folder's `runs.py` and through `tools/harness/batch.py`
  (check, build, analyse, summary); see its docstring.
- Run the tests with their output in a log file and read failures from it:
  `$PY -m unittest discover -s tools/harness/tests > <scratch>/tests.log 2>&1`.
- Renders (`export/`) and probe WAVs are not in the repository. Point every track's clip at the
  one shared probe file (the builders do), and do not copy probes into Live projects.

## Building a device from a note

A note is the starting point for a Suhina device. The device is designed and written up as a spec
in Suhina's own `docs/spec/`, then built in [suhina-daw](https://github.com/suhina-daw/suhina-daw),
whose `AGENTS.md` and ADR 0004 govern the code and whose `docs/spec/device-import.md` gives the
order of work. This section says how closely to follow the note.

### Priorities

Four goals pull against each other. In order:

1. **Quality and performance, first and together.** *Quality* means the device sounds as good as
   Live's, in two senses:
   - **The algorithm.** The kind of algorithm chosen sets how good the effect can sound. A spring
     reverb model, for example, sounds worse than a convolution or a good algorithmic reverb.
     Choose an algorithm in the same class as Live's, and weigh a better-sounding but heavier
     one against the budget rather than taking the cheapest one that roughly fits.
   - **Clean output.** No aliasing, zipper noise, clicks on parameter changes, denormal stalls,
     unstable filters at extreme settings or noise floor that Live does not have, and the same
     sound at every sample rate from 8 kHz to 384 kHz.

   *Performance* means the device is cheap enough to run on every track of a big set (Budget,
   below).
2. **Accuracy and simplicity, second.** *Accuracy* is how closely the device's renders match
   Live's measurements. *Simplicity* is a short algorithm and short code, which is easier to
   check and to keep real-time safe. Simplify only while accuracy stays at an appropriate level
   for what the control does and how audible the difference is; never simplify at the cost of
   quality.

There is no fixed formula for trading these off. Make a judgement call for each device, and
**log every trade-off in the spec's Decisions list**: the choice of algorithm and what was
turned down (an 8-line feedback delay network over a 4-comb Schroeder reverb for a denser tail
at twice the cost), performance given up for quality (2× oversampling to remove aliasing Live
does not have), accuracy given up for simplicity (a one-pole release where Live's curve has a
slight knee), or simplicity given up for accuracy. Each entry says what was chosen, what it
costs (CPU, lines of code, or how far off the renders are), and why.

- **Measuring accuracy.** Render the device's cases through the Suhina device and compare them
  with Live's (`tools/README.md` › 3). `compare.py`'s default tolerances are the reference for
  "close": 0.5 dB for levels, gain curves and responses, 10 % for times, rates and RT60, 0.5 ms
  for tap times. Every measurement outside them goes in the spec's Known differences, with how
  far off it is and the decision that left it there.
- **Measuring quality.** Accuracy runs do not catch every quality problem. Check at least:
  aliasing with a high sine swept at the device's most nonlinear settings, parameter sweeps for
  zipper noise and clicks, silence in and silence out (no denormals, no DC), extreme settings
  for stability, and the cases rendered at 44.1 kHz and at 96 kHz or above for the same result.
- **Exact where it costs nothing.** Ranges, defaults, tapers, step lists and units are
  `[dump 12.4.6]` and `[als 12.4.6]` facts, and the import depends on them. Either the Suhina
  parameter takes the same values, or the import mapping converts them exactly. The trade-offs
  above are for the sound, not for the parameters.
- **Where accuracy matters most, in order:** what you hear in steady state (static gain curves,
  frequency responses, tone); then behaviour over time (attack, release, decay, modulation rate
  and depth); then transient detail, meters and displays. Hold the first to a tighter standard
  than the last when deciding how far to simplify.
- **Budget.** One instance at its default settings should cost under 1 % of one core at 48 kHz
  (a 60 s offline render in under 0.6 s, release build). Devices that are heavy by nature
  (reverbs, the spectral devices, Corpus) may need more; their spec says how much and why.
- **Building blocks.** Use Suhina's `crates/dsp` first, and put a new block there when other
  devices could use it. Prefer textbook designs where they reach the quality bar: RBJ biquads,
  one-pole smoothers and envelope followers, a quadratic soft knee. Oversample where the
  device's nonlinearities would otherwise alias more than Live's. Use FFTs, convolution or large
  tables only where the device works in the spectrum.
- **Latency.** Report the same latency as Live (a lookahead, for example; the analyses' impulse
  offset shows it) and add none that Live does not have, so imported sets stay in time.
- **Ask first** before an approach that is large or slow: convolution, big tables, a model fitted
  to the renders, more than 2× oversampling.

### Reading the note

- **Build on what was observed.** `[dump]`, `[als]` and `[measured]` facts are solid; `[manual]`
  says what a control is for but rarely how it sounds; `[inferred]` and `[source: N]` are guesses
  to check against the renders.
- **A `[measure]` gap does not block the work.** Pick the simplest plausible behaviour, record it
  in the spec's Decisions list, and add a candidate run to the device's `runs.py` if the gap
  matters.
- **Leave out Live's and the harness's quirks.** Some measurements show the export or the
  harness, not the device: the Reverb's Size ignored while Smooth is on, attack times read from
  silent renders, exports that come out early (`tools/README.md` › Limits and the run logs). Copy
  a quirk of the device itself only when it is audible and part of its sound.
- **Design in seconds and hertz, never in samples.** Every render was made at 44.1 kHz, but the
  device runs at any rate (Priorities › Clean output).

### Scope

- **Plan the whole parameter list from the note** before writing the first parameter, so ids and
  order still make sense when the rest lands; ids never change once merged. Ship only parameters
  that do something.
- **UI-only parts can wait:** view modes, meters, draggable displays.

### From note to Suhina

- **The clean-room rules carry over.** The Suhina spec is in Suhina's own words. Only
  `crates/als`, its tests and `docs/spec/` name Live (suhina-daw `AGENTS.md`, rule 8): the device
  crate, its name and its interface do not. DSP ported from a project the note's Implementation
  notes mention needs a GPL-3.0-compatible licence and a row in `ATTRIBUTION.md`.
- **Report the comparison in the PR:** `compare.py`'s "N of M within tolerance" and the Known
  differences and Decisions, beside the conformance tests and golden renders the device PR
  template asks for.
- **Fix the note when building shows it is wrong.** Correct the fact and its tag, or add a run
  for a gap that turned out to matter: the note stays the record of what Live does.
