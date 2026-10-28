# Measurement tools

Tools that fill the `[measure]` gaps in the device notes (`../live-12/audio-effects/`) by
observing Live, and then check a new implementation of a device against what was measured. Two
parts:

| Part | What it does |
|---|---|
| [`probe-device/`](probe-device/) | **Suhina Probe**, a Max for Live audio effect. Passes audio through unchanged; dumps every device's parameters (range, default, steps, display text across the range, so tapers and units) to JSON; builds one track per test case with the device set to the case's values; adds a track per Live audio effect |
| [`harness/`](harness/) | Python: **`measure.py`**, which builds a device's measurement set and analyses its renders; the probe signals (`signals.py`, `probes.py`); a set written directly as an `.als` (`make_als.py`, `als.py`) and checked in Live (`live_check.py`); measurements of renders (`analyse.py`); renders of the same set through the implementation under test (`render_set.py`); and the comparison (`compare.py`) |

Everything here observes the running program through Live's public interfaces (the Live Object
Model as documented by Cycling '74, rendered audio, saved sets). Nothing reads Live's program
files (README › Clean-room rules).

## Setup

```bash
python3 -m venv tools/.venv && tools/.venv/bin/pip install -r tools/harness/requirements.txt
```

Run commands from the repository's root. `PY` below is `tools/.venv/bin/python`.

### Build the Suhina Probe device (only to dump a new Live version's parameters; about two minutes)

The device is kept as text (`suhina_probe.js` and the patcher written by `build_patch.py`), since
an `.amxd` is a binary container. To turn it into a device:

1. `python3 tools/probe-device/build_patch.py` (writes `Suhina Probe.maxpat` and `clipboard.json`).
2. In Live, open the browser's **Max for Live** category and drag **Max Audio Effect** onto an
   audio track. Open the device's title-bar menu (the **⋯** button, rightmost) and choose **Edit
   in Max**; the Max editor opens. (In 12.4.6 the other title-bar buttons are hot-swap and save
   preset, not edit.)
3. In the editor, select everything (**Cmd+A**) and delete it.
4. In a terminal: `pbcopy < tools/probe-device/clipboard.json`. In the editor: **Edit > Paste**.
   The objects appear: `plugin~` wired to `plugout~`, `js suhina_probe.js`, three buttons.
   Max reports `js: can't find file suhina_probe.js` until the next step; that is expected.
5. **File > Save As…** (click the patcher window first, or the item is greyed out): save it as
   `Suhina Probe.amxd` in `tools/probe-device/` (beside `suhina_probe.js`, so the `js` object finds
   it). Close the editor; Live reloads the device and the script loads.
6. Recommended: in the editor, **View > Patcher Inspector**, tick **Open in Presentation**, and
   save. A paste cannot carry that setting, so without it the device view in Live shows the
   patching layout and the status line sits below the visible area. Until then, read the status
   in the editor (**⋯ > Edit in Max**, then lock the patcher with Cmd+E to click the buttons
   there).
7. Optional: click the device's **Freeze** button (in the editor's toolbar) and save again, which
   embeds the script so the device can be copied anywhere.

If pasting does not work in your Max version, build it by hand in the empty editor: a
`plugin~` object wired left-to-left and right-to-right into `plugout~`; a `js suhina_probe.js`
object; message boxes `Dump parameters` → `t b` → `savedialog` → `prepend dump` → js,
`Build cases` → `t b` → `opendialog` → `prepend build` → js, and `populate` → js; and a message
box fed by the js outlet for the status. The js object's console messages start with
`Suhina Probe:` (Max window). In the first run, the Max Console showed these only for actions
taken while the editor was open; Populate and Dump, clicked in the closed device, left nothing
there, so check their results by their effects (tracks, files).

## 1. Dump every device's parameters

1. New Live Set. Drop Suhina Probe on the first audio track.
2. Click **Populate**: one audio track per Live audio effect, each with a fresh copy of it, so all
   at their defaults. This needs `Track.insert_device` (Live 12.3 or later); the status line names
   any it could not add, which you drag in by hand onto their own tracks. `insert_device` loads
   the same factory default preset as the browser (Live's status bar says "Using Default Preset
   ….adv"); a user default preset in `User Library/Defaults/Audio Effects` would replace it, so
   check that folder is empty first.
3. Click **Dump parameters** and choose where to save, for example `reference/dump-12.4.6.json`.

Each device in the dump has `class_name` (the `.als` element name, e.g. `Compressor2`), and each
parameter `name`, `original_name`, `min`, `max`, `value` (the default, on a fresh device),
`default_value` (the reset value; Live gave one for every parameter in 12.4.6), `is_quantized`, `value_items` and `samples`: `[value,
display text]` at 65 evenly spaced values (send `samples 257` to the js object for finer). The
samples are the control's display curve, so they give the taper and the unit:

```bash
$PY tools/harness/cases.py list reference/dump-12.4.6.json                 # every device
$PY tools/harness/cases.py list reference/dump-12.4.6.json --device Compressor   # its parameters, ranges, tapers
```

`value` is what the loaded preset sets and `default_value` what double-click or Delete restores;
they can differ (Compressor loads with Env Mode Log but resets to Lin). The reset value of
`Device On` reads 0 (off) on every device, an API quirk to ignore.

Copy what the dump settles into the device's note: replace `[measure]` with the value and the
tag `[dump 12.4.6]`. Save the populated set too: its device elements hold the parameters under
their `.als` names in stored units (Compressor `Threshold` = 1 is linear gain, 0 dB; `Attack` = 1
is ms), which the dump's 0..1 internal values do not show. `reference/dump-12.4.6-summary/`
has one readable file per device with both.

**MIDI effects.** The probe's Populate adds only audio effects, but its dump reads every track,
MIDI tracks included. `harness/populate_midi.py` makes the set for the MIDI effects as a file:
`write` puts the probe and one MIDI track per MIDI effect into a new set, `live_check.py open`
loads it, and `load` puts each effect on its track from the browser through the Remote Script
(the factory default preset). Then Dump parameters and save the set, as above. The 12.4.6 run
is `reference/dump-midi-12.4.6.json`, `reference/populate-midi-12.4.6.als` and the
`Midi*.txt` summaries; its docstring has the commands.


## 2. Measure a device's behaviour

A device's runs are in `devices/<device>/runs.py` (`measure.py`'s docstring has the format): each
run is a question ("slope above the threshold for Ratio 2 to inf"), the probe that answers it
and the cases, each a set of parameter values. `measure.py` turns the runs into one Live Set, so
no case is built by hand.

```bash
PY=tools/.venv/bin/python
$PY tools/harness/measure.py list                          # devices and runs
$PY tools/harness/measure.py list compressor               # one device's runs and questions
$PY tools/harness/measure.py check compressor              # every run's values, without Live
$PY tools/harness/measure.py build compressor              # work/sets/compressor/compressor.als
$PY tools/harness/live_check.py open work/sets/compressor/compressor.als
$PY tools/harness/live_check.py verify work/sets/compressor/compressor.cases.json   # optional
#   File > Export Audio/Video (below)
$PY tools/harness/measure.py analyse compressor            # devices/29.09-compressor/results/
```

A DEVICE argument is a folder of `devices/` or any part of its name; none means every audio
effect (about 2700 tracks, an hour of export), and `--run` picks runs. `build` writes each run's
cases file into `devices/<device>/cases/`, makes the probes it needs in `probes/`
(`probes.py`: the main probe with 2, 10 or 30 s of silence after each signal, the extended and
fifth probes, the side-chain keys; all at 44.1 kHz) and prints the export name and length for each
probe it used.

**Opening the set.** With the AbletonMCP Remote Script installed (2b) `live_check.py open` loads
the set and waits for it; without it, double-click the `.als`. It is a Live Project (the empty
`Ableton Project Info` folder beside it), which Live needs to load the probe clips; they play the
files in `probes/`, so move nothing there while Live has the set open. Live 12.4.6 and
12.4.7 differ in places (the notes' `[measured 12.4.6]` and `[measured 12.4.7]` tags); a set
renders in whichever version opens it.

**Export** (the one step that needs Live's window): File > Export Audio/Video, Rendered Track
**All Individual Tracks** (or **Selected Tracks Only** for one probe's tracks), from 1.1.1, for the
length `build` prints (the probe's length in bars at 120 BPM), WAV, 32-bit, the set's sample rate
(44.1 kHz), Normalize off, Dither off (greyed out at 32-bit), Create Analysis File off, into
`work/sets/<name>/export/`, with the export name `build` prints. Live names the files `<export
name> <track name>.wav`, adds `<export name>.wav` for the main mix (ignored) and writes silent files
for tracks without clips. When a set uses more than one probe, export each probe's tracks on
their own under `<name>-<probe>`, or every track at once under `<name>` at the longest length and
add `--trim` to `analyse`.

**Analyse** measures every render (`analyse.py`) and writes `devices/<device>/results/<track>.json`
for each (kept in the repository), the CSV views and impulse response into `extras/`, and files the
render in `renders/<track>.wav` (the last two are not in the repository; `--no-file` leaves the
render). The offset of Live's export against the probe is taken from the `bypass` renders of each
probe's tracks; Live has exported a whole set 40 ms early, so check the line `analyse` prints. A
render that is not there is reported, so a partial export is measured as far as it goes and
`analyse` run again afterwards finds the renders already filed.

Which signal answers which question:

| Question in a note | Read |
|---|---|
| range, default, steps, taper, unit | the dump |
| filter shape, slope, EQ curve | `response.sweep_db` (time-invariant devices), `response.noise_db` (modulated ones) |
| delay times, feedback, echoes | `impulse.taps` |
| reverb or resonator decay | `impulse.rt60_s`, the `.ir.wav` in `extras/` |
| compressor or distortion curve, makeup, ceiling | `static` (output and gain per input level, THD and harmonics) |
| attack and release | `dynamics` (63 % and 90 % times; resolution one cycle of the tone, 1 ms) |
| LFO rate and depth (tremolo, pan, chorus, vibrato) | `modulation` (AM rate/depth, FM rate/depth in cents, L/R envelope correlation) |
| width, pan, channel modes | `stereo` |
| noise, crackle | `silence` |
| latency | Live's own readout (hover the device title), or `--align xcorr` on a render with compensation off |

`signals.py`'s docstring lists the probe's signals, and `probes/<name>.json` says where each
starts. Analysing one render by hand: `$PY tools/harness/analyse.py probes/gap2.json
<render>.wav -o <folder>`.

**Adding a run.** Add a dict to the device's `runs.py`, `check` it, `build` and measure it as
above. To look at a device's parameters first: `$PY tools/harness/cases.py list
reference/dump-12.4.6.json --device Compressor`. Old runs stay: a new run answers a new question
and the note records it.

## 2b. How the set is written, and calibrating a device

`make_als.py` (which `measure.py build` calls) writes the cases of any number of cases files, for
any calibrated devices, into one Live Set: one track per case, named `<run> <case id>`, holding the
probe clip and a fresh copy of the device with the case's values. The set is opened in Live and
exported once for a whole batch of runs; the Suhina Probe is not needed.

A set stores each parameter in its own units, under an element name that often differs from the
API name and in a different order (Compressor's Output is `Gain`, EQ Eight's Adaptive Q comes
last), so each device is calibrated once. Live reports what each stored element means through
the [AbletonMCP](https://github.com/ahujasid/ableton-mcp) Remote Script (MIT), which
`live_check.py` talks to on 127.0.0.1:9877.

**Setup (once).** Install only the Remote Script, not the project's MCP server (that one records
sessions to a remote dataset when it gets consent; the Remote Script makes no outbound
connections): take `MCP_Server/bundled_ableton_remote_script/AbletonMCP_init.py` from the
`ableton-mcp` wheel on PyPI (`pip download --no-deps ableton-mcp`) and copy it to
`~/Music/Ableton/User Library/Remote Scripts/AbletonMCP/__init__.py`. Restart Live, then in
**Settings > Link, Tempo & MIDI** choose **AbletonMCP** as a Control Surface, Input and Output
None. `nc -z 127.0.0.1 9877` succeeds once it is listening.

**Driving Live through the Remote Script.** Everything up to the export goes through the
Remote Script, not Live's window: `live_check.py open <set>.als` opens a set (`open -a`) and waits
until the script lists its tracks (the number, and the first and last names), `read` dumps every
track's devices, `verify` checks a generated set. Live replaces the open set without asking only
when that one has no unsaved changes; if `open` times out, a dialog is waiting in Live. Live's API
has no audio export and the script cannot arm, route or record, so the export (2) is the
one step done in the UI. Agents ask the user before taking over Live's window for it
(`AGENTS.md`).

**Calibrate a device (once per device):**

```bash
$PY tools/harness/make_als.py calibrate --device Compressor -o work/calibrate/compressor.als
$PY tools/harness/live_check.py open work/calibrate/compressor.als
$PY tools/harness/live_check.py read -o work/calibrate/compressor.read.json
$PY tools/harness/make_als.py map work/calibrate/compressor.calibration.json \
    work/calibrate/compressor.read.json
```

The calibration set has a `ref <class>` track (the factory default) and one `cal <class>
<element>` track per parameter element with only that element changed. `map` finds the one API
parameter that moved on each track and works out how an API value becomes the stored value:

| `convert` | Stored value | Example |
|---|---|---|
| `same` | the API value | Compressor Output (`Gain`, dB) |
| `integer` | the API value, rounded: Live truncates a stored fraction on loading | Corpus Transpose, Resonators I Note |
| `base`, `ms`, `percent`, `gain` | the display's number in base units, × 1000 for ms, / 100 for %, or dB as linear gain (each only with that unit) | Compressor Ratio, Attack, Threshold |
| `linear` | a straight line from the API range onto the element's `MidiControllerRange` (`range`: API min, max, element min, max) | Saturator Drive (0 .. 1 onto −36 .. 36) |
| `bool`, `offset` | on/off, or the API index plus a constant | Device On, Compressor Model |

`linear` is chosen over a display conversion when the dump's display lies on that line at every
sample, since it is exact where the display is rounded. The result goes to
`reference/als-map-12.4.6.json`. Elements that move no API parameter (the Compressor's
`LegacyModel`) are listed as unmatched and never set. Re-running `map` for another device
replaces that device's entry.

The calibration sets are scratch files (`work/calibrate/`, not kept; the result is the map). All 42
Live audio effects are mapped; see [All effects calibrated](#all-effects-calibrated-live-1246-2026-10-18) for what has no element or no
parameter.

**Build and check a measurement set by hand** (`measure.py build` does this for a device's runs):

```bash
$PY tools/harness/make_als.py build devices/29.09-compressor/cases/compressor-threshold.json \
    devices/29.09-compressor/cases/compressor-attack.json -o work/compressor-gen.als
$PY tools/harness/live_check.py open work/compressor-gen.als
$PY tools/harness/live_check.py verify work/compressor-gen.cases.json \
    -o work/compressor-gen.verified.json
```

`build` writes the set and `<set>.cases.json` (per track: device, and per case parameter the
API value, element and stored value). `verify` reads every track back from Live. It checks each
case parameter against its API value, and every other parameter against the dump's default,
which is where a wrongly mapped element shows. With `-o` it writes what Live reports (`live`)
beside each value: the record to analyse against, as the record of what each case holds. Export as in (2) under one
export name; each run's files are then `<export> <run> <case id>.wav`.

- **Values.** A `display` spec in base units is converted exactly (Threshold `display:-20` is
  stored as 0.1), and so is any value through `same`, `integer`, `linear`, `bool` or `offset`.
  A `display` spec through `linear` inverts the line, by the display conversion that puts every
  dump sample on it (Saturator Drive `display:-12` is stored as −12 at API 1/3, where the dump's
  `-12 dB` sample is at 0.328125, −12.375 dB); the three whose display is on no such line
  (Saturator Color Amt Low and Hi, Shifter Pitch Fine) go through the sampled display curve.
  Before this, every `linear` display went through the curve, so the top 100 runs stored a
  rounded sample there (Saturator Drive and Output, Limiter Output); the device notes give
  the values stored.
  A `norm` or plain value through a display conversion goes through the dump's sampled display
  curve (exact at the default and at the samples), so it lands within the display's rounding of
  the target: three figures, below 0.1 % of the range for the Compressor. A display shown to
  two places is too coarse to interpolate between, so where the samples all lie within their
  rounding of one exponential (Auto Shift's LFO Rate, 0.01 to 20 Hz) the value comes from that
  exponential: norm 0.25 is written as 0.0669 Hz and Live reads back 0.25, where interpolating
  the displayed `0.07 Hz` read back 0.256. `{"stored": x}` writes a stored value as it is, for a parameter the map has no
  conversion for. A display-given value's expected API value is only known to one sample step
  (1/64 of the range) except on a `linear` line, and `verify` allows that much for every
  display-given value.
- **The template** (`--template`, default `tools/harness/data/template.als`, a set Live saved with one probe clip, Warp off, at 120 BPM)
  supplies the audio track with the probe clip (Warp off), the tempo and the main track. Its
  other tracks and its return tracks are dropped (`--keep-returns` keeps the returns). The clip
  is pointed at `--probe` (a name from `probes.py`, default `gap2`, or a WAV) and fitted to its length, so a
  reverb run can use `gap30`. The probe must have the set's sample rate. A cases
  file can name its own probe (`"probe"`: a name from `probes.py`), so runs with different probes can share a set; a run
  that needs another tempo goes in another set.
- **`--share`** gives one track to every case whose device is stored identically with the same
  probe (every run's `bypass` of a device, a `default` that another run also has), named after
  the first such case; `<set>.cases.json` records each case's `track`, and `verify` follows it.
- **The set is a Live Project.** Live 12.4.6 loads no sample of a set that is not in a Project
  folder, whatever the clip's Path says: every clip shows Sample Offline and Live's `Log.txt`
  says `The file "probe.wav" could not be opened`. `build` writes an empty
  `Ableton Project Info/` beside each set for that. `verify` reads only devices,
  so it does not catch an offline clip; a silent `bypass` render does.
- **Export names.** Live writes a `/` in a track name as `_` in the exported file's name.
- **Checked in Live 12.4.6.** A 37-track set built through the map (`verify` reported 0 problems) covered `linear` (Saturator Drive and
  Color Amt Low and Hi, Amp Bass, Reverb Diffuse Level, Roar Env Gain), `integer` (Corpus Transpose -18.6 is written and read back as -19, Resonators I Note
  40.4 as 40), `base` (Auto Shift LFO Rate), nested elements (EQ Eight band 3) and `gain`
  (External Audio Effect Input Gain), each by norm and by display.
- **Added for the third set:** stored elements (`"@path"`: routing modes, oversampling switches, the
  Vocoder carrier), automation lanes (`{"auto": ...}`), audio key tracks for side-chains and MIDI
  tracks for the MIDI modes (make_als.py's docstring); their effect on the audio was checked in the third set's renders (Live does not read stored elements back).
- **Not covered yet:** devices inside racks, the Spread of Shifter, and controls that are neither a
  parameter nor a stored element.

Measurement runs, devices and probes are described in 2; the batches made so far are listed in the
README's Measurement sets.

## 3. Compare an implementation with Live

Render every case through the implementation, one WAV per case named by its case id, analyse
those renders the same way, and compare. Two ways to get the renders:

- **From the saved set**, if the implementation can import and render a Live Set offline: give
  `render_set.py` its renderer's command line. It renders the set (`measure.py build compressor`
  makes `work/sets/compressor/compressor.als`) once per track with every other track switched off.

  ```bash
  $PY tools/harness/render_set.py work/sets/compressor/compressor.als \
      -o work/mine/compressor/renders \
      --command "<renderer> {set} -o {out} --sample-rate {rate}" --rate 44100
  ```

- **From the cases file**, if it cannot import Live Sets yet: play the run's probe
  (`probes/<probe>.wav`, named in the cases file) through the device with each case's
  settings and save `<case id>.wav`. `devices/29.09-compressor/cases/compressor-threshold.json`
  lists every case's parameters by Live's name; the device's note maps those to stored units
  (Controls, Implementation notes).

```bash
$PY tools/harness/analyse.py probes/gap2.json work/mine/compressor/renders/*.wav \
    -o work/mine/compressor/results
$PY tools/harness/compare.py devices/29.09-compressor/results work/mine/compressor/results \
    --cases devices/29.09-compressor/cases/compressor-threshold.json
```

A device the implementation does not have yet must not pass audio through silently: the
comparison would then show every case as equal to `bypass`, which is easy to misread. `compare.py` pairs
results by case id, prints every measurement out of tolerance (`-v` for all of them;
`--tol-db`, `--tol-rel`, `--tol-ms` set the limits) and exits 1 when any case differs.

## Tests

```bash
$PY -m unittest discover -s tools/harness/tests     # about a minute
node --test tools/probe-device/test                  # the probe script against a mocked Live API
```

The harness tests run synthetic devices with known behaviour (gain, echoes, a one-pole low-pass,
a hard clipper, a compressor with 10 ms attack and 100 ms release, tremolo, vibrato, a decaying
noise reverb, swapped channels) and check that the measurements recover them. The probe test runs
`suhina_probe.js` in Node with mocks of `LiveAPI`, `File` and `Task`.

## Quirks of Live and of the harness

- **Size set through the API is ignored by the export while Smooth is Fast or Slow** (Reverb).
  Five Size values gave bit-identical renders; with Smooth = None they differ. Put
  `"Size Smoothing": {"item": "None"}` in every case that sets Room Size.
- **An export can come out early.** Three of five Reverb exports were 1764 samples (40.00 ms)
  ahead of the probe, bypass included; cause not found. `analyse` takes the offset from the
  `bypass` renders and prints it; check that line. `analyse.py --align -1764` fixes one by hand.
- **Dropping a WAV into an empty set warps it and changes the tempo.** The built sets avoid this
  (Warp off, 120 BPM); do it the same way for any hand-made set.
- **Export dialog:** the Render Length field keeps its last value; set it to the length `build`
  prints each time. The default set's four tracks and two returns export as silent files.
- **Harness:** `impulse.rt60_s` reads far too short for a reverb with early reflections; refit
  from the `.ir.wav`. `modulation` figures for a tone through a reverb are a rough spread, not a
  clean depth. On a silent render (a track with no clip) `analyse.py` still reports attack and
  release times (about 0.7 ms) from noise; ignore `dynamics` when `impulse.peak_db` is −240.
- **A setting can be stored and read back and still not reach the audio.** Before reading a case,
  check that its render is not bit-identical to the `default` (or, for a lane, the `bypass`). In the
  first sets Auto Pan-Tremolo's Waveform (all eight cases rendered as Sine) and the Looper's stored State
  did not reach the render; stored elements (`"@..."`) later did work (Roar's routing, the
  oversampling switches, Spectral Time's Resolution, the Vocoder's carrier) but Live does not read
  them back, so `verify` cannot confirm them. Some bit-identical pairs are genuine (EQ Three Mid off
  and -inf; Gate Floor 0 dB is the bypass; Overdrive Tone at Dry/Wet 0 %).
- **A display value is stored at the nearest step.** A display with two significant digits cannot
  say which API value it means, so cases such as Limiter Ceiling -12 dB, Saturator Drive -12 dB
  (stored as -12.375) and Shifter Env Amount 0 st can verify off the requested API value. The
  notes quote the stored value, and `verify -o` records what Live holds.
- **Live names two exports the same file** when two tracks have the same name (`...-1.wav`); keep
  case ids unique within a run.
- **The export is delay-compensated**, so a device's latency is hidden (Compressor's lookahead,
  Spectral Resonator, Amp, the oversampling of Hi-Quality): look for a response that begins before
  the impulse. A render of 88.2 kHz resampled to 44.1 kHz did not play every automation lane (a
  Looper State lane left the device idle): render at the project's 44.1 kHz.
- **Silent renders can be right** (a gate closed, Beat Repeat idling, Volume 0, Utility Gain -inf,
  Amp Input Gain 0).
- **Parameter names:** Corpus has two parameters named Width (`Width` is the filter bandwidth,
  `Width #2` the stereo width); Glue Compressor's Ratio, Attack and Release are set by index.
- **Roar loads in Multi Band** (stored routing 3), so a shaper or filter run that does not set the
  routing reaches only the low band.
- **Figures beyond `analyse.py`.** Reverbs, delay swings, partials and pitch tracking need their own
  readings (Schroeder curves per band, Hilbert envelopes, cross-correlation, comb scores); the notes
  say how each was read. `analyse.py`'s `rt60_s` and `noise_db` (186 ms window) do not suit reverbs.
- **A save or open panel takes a path only through Go to Folder** (Cmd+Shift+G).


## Limits

- Attack and release shorter than one cycle of the 1 kHz tone (1 ms) read as about 0.5 ms.
- The sweep response assumes a time-invariant device; for modulated devices read `noise_db`.
- `build` finds a parameter by `name` or `original_name`; when two parameters of a device share
  a name, the first one wins.
- `--display` finds values by bisection and assumes the control's display is monotonic.
- `analyse.py`'s `rt60_s` and `noise_db` (186 ms window) do not suit reverbs, and its attack,
  release and FM figures failed for several devices in the top 100 runs; the device notes say
  where and give the figures computed from the renders instead.

### All effects calibrated (Live 12.4.6, 2026-10-18)

One calibration set per device, read through the Remote Script one after another (`open -a`,
wait until Live lists the set's tracks, `live_check.py read`). All 41 sets besides the
Compressor's opened with no dialog or missing media, and every track held its device with the
dump's parameter count. `map` matched every API parameter of every device to exactly one element,
with no "several moved" and no "matched both". The two conversions added for this run
(`integer`, `linear`) were the only fixes `map` needed; before them, five parameters had "no
conversion fits" (Corpus Transpose, Resonators I Note, Spectral Resonator Note, Saturator Color
Amt Low and Hi), and `gain` overflowed on displays in Hz.

- **Elements without a parameter**, never set by `build`: Compressor `LegacyModel`,
  `LegacyEnvFollowerMode`; Delay `DelayLine_SimpleDelayTimeL`/`R` and
  `DelayLine_PingPongDelayTimeL`/`R` (older delay times; the API's times are other elements);
  EQ Eight `SpectrumAnalyzer/On` (the display's analyser); Tuner `TuningFreq` (the reference
  pitch, which the API does not show); Utility `LegacyGain`, `MidSideBalance`.
- **Nested elements work as paths:** EQ Eight's bands (`Bands.0/ParameterA/Freq`, all 84),
  Roar's stages (91) and Hybrid Reverb (54) mapped in full, as did External Audio Effect
  (`InputHelper/Volume`, `OutputHelper/Volume` as gains).
- **Not parameters, so not in the map:** External Audio Effect's audio routing (To and From
  the hardware), Hybrid Reverb's impulse response choice, side-chain sources. Spectrum and Tuner
  have only Device On.
- **Not calibrated:** Max Audio Effect (`MxDeviceAudioEffect`, the Suhina Probe on the dump's
  `3-Audio` track): a Max for Live device, not a Live audio effect.
- **Calibration values:** every element without a `MidiControllerRange` is a bool in these 42
  effects; an enum at the top of its range steps down instead of up.
