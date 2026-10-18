# Measurement tools

Tools that fill the `[measure]` gaps in the device notes (`../live-12/audio-effects/`) by
observing Live, and then check a new implementation of a device against what was measured. Two
parts:

| Part | What it does |
|---|---|
| [`probe-device/`](probe-device/) | **Suhina Probe**, a Max for Live audio effect. Passes audio through unchanged; dumps every device's parameters (range, default, steps, display text across the range, so tapers and units) to JSON; builds one track per test case with the device set to the case's values; adds a track per Live audio effect |
| [`harness/`](harness/) | Python: the probe signal (`signals.py`), case files from a dump (`cases.py`), a measurement set written directly as an `.als` (`make_als.py`, `als.py`) and checked in Live (`live_check.py`), measurements of renders (`analyse.py`), renders of the same set through the implementation under test (`render_set.py`), and the comparison (`compare.py`) |

Everything here observes the running program through Live's public interfaces (the Live Object
Model as documented by Cycling '74, rendered audio, saved sets). Nothing reads Live's program
files (README › Clean-room rules).

## Setup

```bash
python3 -m venv tools/.venv && tools/.venv/bin/pip install -r tools/harness/requirements.txt
```

Run commands from this folder (`suhina-resources`). `PY` below is `tools/.venv/bin/python`.

### Build the Suhina Probe device (once, about two minutes)

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
3. Click **Dump parameters** and choose where to save, for example `measurements/dump-12.4.6.json`.

Each device in the dump has `class_name` (the `.als` element name, e.g. `Compressor2`), and each
parameter `name`, `original_name`, `min`, `max`, `value` (the default, on a fresh device),
`default_value` (the reset value; Live gave one for every parameter in 12.4.6), `is_quantized`, `value_items` and `samples`: `[value,
display text]` at 65 evenly spaced values (send `samples 257` to the js object for finer). The
samples are the control's display curve, so they give the taper and the unit:

```bash
$PY tools/harness/cases.py list measurements/dump-12.4.6.json                 # every device
$PY tools/harness/cases.py list measurements/dump-12.4.6.json --device Compressor   # its parameters, ranges, tapers
```

`value` is what the loaded preset sets and `default_value` what double-click or Delete restores;
they can differ (Compressor loads with Env Mode Log but resets to Lin). The reset value of
`Device On` reads 0 (off) on every device, an API quirk to ignore.

Copy what the dump settles into the device's note: replace `[measure]` with the value and the
tag `[dump 12.4.6]`. Save the populated set too: its device elements hold the parameters under
their `.als` names in stored units (Compressor `Threshold` = 1 is linear gain, 0 dB; `Attack` = 1
is ms), which the dump's 0..1 internal values do not show. `measurements/dump-12.4.6-summary/`
has one readable file per device with both.

**MIDI effects.** The probe's Populate adds only audio effects, but its dump reads every track,
MIDI tracks included. `harness/populate_midi.py` makes the set for the MIDI effects as a file:
`write` puts the probe and one MIDI track per MIDI effect into a new set, `live_check.py open`
loads it, and `load` puts each effect on its track from the browser through the Remote Script
(the factory default preset). Then Dump parameters and save the set, as above. The 12.4.6 run
is `measurements/dump-midi-12.4.6.json`, `measurements/populate-midi-12.4.6.als` and the
`Midi*.txt` summaries; its docstring has the commands.

## 2. Measure the device's behaviour

1. Make the probe signal at the set's sample rate (use `--gap 10` or more for reverbs and long
   delays, so tails do not run into the next signal):

   ```bash
   $PY tools/harness/signals.py -o measurements/probe.wav --rate 48000 --gap 2
   ```

   `probe.json` beside it says where each test signal starts (impulse, sweep, level staircase,
   level bursts, steady tone, noise, left-only, right-only, silence).
2. New Live Set at 120 BPM, 48 kHz (**Settings > Audio**). Drag `probe.wav` to the start of an
   audio track in the Arrangement. In the clip's view turn **Warp** off, so the file plays
   untouched. Put Suhina Probe on the track, and the device to measure right of it.
   - Dropping the file into an empty set warps it and **changes the set's tempo** to fit (82.14
     BPM in the first run). Turn Warp off first, then type 120 into the tempo field.
   - Some audio outputs fix the rate: with Bluetooth headphones as output, Live offers only
     44.1 kHz. Everything here works at any rate as long as it is the same throughout: make the
     probe with `--rate 44100` and render the implementation's cases at 44.1 kHz too. The first run used
     44.1 kHz for this reason.
   - Easiest way to reach `probe.wav` and the probe from Live's browser without adding a folder to
     Places: save the new set first (Live makes `<name> Project/`), copy `probe.wav`, `Suhina
     Probe.amxd` and `suhina_probe.js` into that folder, then use the browser's **Current
     Project**.
3. Make the cases, for example the Compressor's Threshold at seven values with Ratio fixed:

   ```bash
   $PY tools/harness/cases.py sweep measurements/dump-12.4.6.json --device Compressor \
       --param Threshold --points 7 --set "Ratio=display:4" \
       -o measurements/29.09-compressor/compressor-threshold.json
   ```

   Values: `--points N` steps evenly through the internal range, `--display=-40,-30,-20` picks
   values by what the control shows (Hz, s, dB, %), a quantized parameter gets one case per item.
   Every file starts with `bypass` (device off) and `default`. Each device's runs go in its own
   folder under `measurements/`, named like its note (`29.09-compressor/` for the Compressor).
4. Click **Build cases** on the probe and choose the cases file. One track per case appears
   under the template, named by case id; `compressor-threshold.built.json` records the value and
   display text each parameter actually got, and any parameter it could not set.
5. **File > Export Audio/Video**: Rendered Track **All Individual Tracks**, from 1.1.1 for the
   length of the probe (the manifest's `length` / `rate` seconds), WAV, 32-bit, the same sample
   rate, Normalize off, Dither off (greyed out at 32-bit), Create Analysis File off. The probe is
   46.75 s, so 24 bars at 120 BPM. Export into the device's `export/` folder
   (`measurements/29.09-compressor/export/`) and save the set at the top of its folder
   (`compressor-threshold.als`). Live names the files `<export name> <track name>.wav` (e.g.
   `compressor-threshold bypass.wav`), adds `<export name>.wav` for the main mix, writes silent
   files for audio and return tracks without clips, and skips MIDI tracks without instruments.
   `compare.py --cases` pairs these by the case id at the end of the name, as it is.
6. Measure:

   ```bash
   $PY tools/harness/analyse.py measurements/probe.json measurements/29.09-compressor/export/*.wav \
       -o measurements/29.09-compressor/live
   ```

   Per render: `<name>.json` (impulse taps, RT60, frequency response from sweep and noise, static
   gain curve with THD, attack and release times, amplitude and pitch modulation, stereo matrix,
   output with no input), and `<name>.response.csv`, `.static.csv`, `.envelope.csv`, `.ir.wav`.
   Live's export is delay-compensated, so renders line up with the probe; add `--align xcorr` if
   one does not.

Which signal answers which question:

| Question in a note | Read |
|---|---|
| range, default, steps, taper, unit | the dump |
| filter shape, slope, EQ curve | `response.sweep_db` (time-invariant devices), `response.noise_db` (modulated ones) |
| delay times, feedback, echoes | `impulse.taps` |
| reverb or resonator decay | `impulse.rt60_s`, `.ir.wav` |
| compressor or distortion curve, makeup, ceiling | `static` (output and gain per input level, THD and harmonics) |
| attack and release | `dynamics` (63 % and 90 % times; resolution one cycle of the tone, 1 ms) |
| LFO rate and depth (tremolo, pan, chorus, vibrato) | `modulation` (AM rate/depth, FM rate/depth in cents, L/R envelope correlation) |
| width, pan, channel modes | `stereo` |
| noise, crackle | `silence` |
| latency | Live's own readout (hover the device title), or `--align xcorr` on a render with compensation off |

## 2b. Write the measurement set as one `.als` instead

`make_als.py` writes the cases of any number of cases files, for any calibrated devices, into one
Live Set: one track per case, named `<run> <case id>`, holding the probe clip and a fresh copy of
the device with the case's values. It replaces steps 2.2 to 2.4 (no dragging the probe in, no
Build cases). The set still has to be opened in Live and exported (step 2.5), but once for a whole
batch of runs.

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
has no audio export and the script cannot arm, route or record, so the export (step 2.5) is the
one step done in the UI. Agents ask the user before taking over Live's window for it
(`AGENTS.md`).

**Calibrate a device (once per device):**

```bash
$PY tools/harness/make_als.py calibrate --device Compressor -o measurements/29.09-compressor/compressor-calibrate.als
$PY tools/harness/live_check.py open measurements/29.09-compressor/compressor-calibrate.als
$PY tools/harness/live_check.py read -o measurements/29.09-compressor/compressor-calibrate.read.json
$PY tools/harness/make_als.py map measurements/29.09-compressor/compressor-calibrate.calibration.json \
    measurements/29.09-compressor/compressor-calibrate.read.json
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
`measurements/als-map-12.4.6.json`. Elements that move no API parameter (the Compressor's
`LegacyModel`) are listed as unmatched and never set. Re-running `map` for another device
replaces that device's entry.

The calibration files of each device are `measurements/29.NN-<device>/<device>-calibrate.*`
(`.als`, `.calibration.json`, `.read.json`). All 42 Live audio effects are mapped; see [All
effects calibrated](#all-effects-calibrated-live-1246-2026-10-18) for what has no element or no
parameter.

**Build and check a measurement set:**

```bash
$PY tools/harness/make_als.py build measurements/29.09-compressor/compressor-threshold.json \
    measurements/29.09-compressor/compressor-attack-gen.json -o measurements/29.09-compressor/compressor-gen.als
$PY tools/harness/live_check.py open measurements/29.09-compressor/compressor-gen.als
$PY tools/harness/live_check.py verify measurements/29.09-compressor/compressor-gen.cases.json \
    -o measurements/29.09-compressor/compressor-gen.verified.json
```

`build` writes the set and `<set>.cases.json` (per track: device, and per case parameter the
API value, element and stored value). `verify` reads every track back from Live. It checks each
case parameter against its API value, and every other parameter against the dump's default,
which is where a wrongly mapped element shows. With `-o` it writes what Live reports (`live`)
beside each value: the record to analyse against, in place of `<run>.built.json`. Export as in
step 2.5 under one export name. Each run's files are then `<export> <run> <case id>.wav`, so
analyse one run with the glob `"<export> <run> "*.wav`, and `compare.py --cases` takes the
`.verified.json`.

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
- **The template** (`--template`, default `measurements/29.09-compressor/compressor-threshold.als`)
  supplies the audio track with the probe clip (Warp off), the tempo and the main track. Its
  other tracks and its return tracks are dropped (`--keep-returns` keeps the returns). The clip
  is pointed at `--probe` (default `measurements/probe.wav`) and fitted to its length, so a
  reverb run can use `probe-gap30/probe.wav`. The probe must have the set's sample rate. A cases
  file can name its own probe (`"probe"`), so runs with different probes can share a set; a run
  that needs another tempo goes in another set.
- **`--share`** gives one track to every case whose device is stored identically with the same
  probe (every run's `bypass` of a device, a `default` that another run also has), named after
  the first such case; `<set>.cases.json` records each case's `track`, and `verify` follows it.
- **The set is a Live Project.** Live 12.4.6 loads no sample of a set that is not in a Project
  folder, whatever the clip's Path says: every clip shows Sample Offline and Live's `Log.txt`
  says `The file "probe.wav" could not be opened`. `build` writes an empty
  `Ableton Project Info/` beside each set for that (ignored by git). `verify` reads only devices,
  so it does not catch an offline clip; a silent `bypass` render does.
- **Export names.** Live writes a `/` in a track name as `_` in the exported file's name.
- **Checked in Live 12.4.6.** `measurements/map-check/` builds into one 37-track set
  (`map-check-gen.als`; `verify` reports 0 problems) that covers `linear` (Saturator Drive and
  Color Amt Low and Hi, Amp Bass, Reverb Diffuse Level, Roar Env Gain), `integer` (Corpus Transpose -18.6 is written and read back as -19, Resonators I Note
  40.4 as 40), `base` (Auto Shift LFO Rate), nested elements (EQ Eight band 3) and `gain`
  (External Audio Effect Input Gain), each by norm and by display.
- **Not covered yet:** automation (Freeze, Smooth), side-chain routing, MIDI-driven devices
  (Vocoder carrier, Spectral Resonator MIDI), and devices inside racks.

### Many devices' runs in one set: `batch.py`

For more than a few runs, write them as data and let `batch.py` make the cases files, the set and
the analyses (its docstring has the formats):

```bash
$PY tools/harness/batch.py check                                        # every device's runs.py
$PY tools/harness/batch.py build measurements/top100/selection.json     # cases files and one set
$PY tools/harness/live_check.py open measurements/top100/top100.als --timeout 900
$PY tools/harness/live_check.py verify measurements/top100/top100.cases.json -o measurements/top100/top100.verified.json
# export (step 2.5), then
$PY tools/harness/batch.py analyse measurements/top100/selection.json --export measurements/top100/export --trim
$PY tools/harness/batch.py summary measurements/top100/selection.json [run ...]
```

- **Runs** live in each device folder's `runs.py` (`DEVICE` and `RUNS`: name, the Measurement
  plan step it answers, the question, which parts of `analyse.py`'s result answer it, the probe,
  a `base` and the cases). Every run also gets `bypass` and `default`. `check` works out every
  value against the dump and the map, so a wrong name or impossible value shows before Live does.
- **A selection** (`selection.json`) names the set, its probes and the runs. `build` writes each
  run's cases file beside its `runs.py`, then one set with `make_als.py build --share`, the
  tracks ordered by probe, every clip pointing at its group's one probe file.
- **Export** each probe group's tracks on their own (Selected Tracks Only, the probe's length,
  name `<set>` for the first probe and `<set>-<probe>` for the others), or all tracks at once
  under `<set>` at the longest probe's length; then `analyse --trim` cuts each render back to its
  probe's length and keeps the disk use down (690 tracks at 60 bars: 27 GB, 11 GB trimmed).
- **Analyse** takes each probe group's offset from its `bypass` renders and writes every track's
  analysis into its device's `live/`; `<set>.analysis.json` records the offsets and each case's
  result file. `summary` prints each run's `read` figures per case.
- **First used** for the top 100 runs (`measurements/top100/README.md`): 100 runs of 37 devices,
  805 cases on 690 tracks; Live 12.4.6 opened the set in 30 s and `verify` matched 802 cases.

## 3. Compare an implementation with Live

Render every case through the implementation, one WAV per case named by its case id, analyse
those renders the same way, and compare. Two ways to get the renders:

- **From the saved set**, if the implementation can import and render a Live Set offline: give
  `render_set.py` its renderer's command line. It renders the set once per track with every other
  track switched off.

  ```bash
  $PY tools/harness/render_set.py measurements/29.09-compressor/compressor-threshold.als \
      -o measurements/29.09-compressor/mine-renders \
      --command "<renderer> {set} -o {out} --sample-rate {rate}" --rate 44100
  ```

- **From the cases file**, if it cannot import Live Sets yet: play `probe.wav` through the device
  with each case's settings and save `<case id>.wav`. `compressor-threshold.built.json` lists
  every case's parameters by Live's name, with the value and display text Live gave them; the
  device's note maps those to stored units (Controls, Implementation notes).

```bash
$PY tools/harness/analyse.py measurements/probe.json measurements/29.09-compressor/mine-renders/*.wav \
    -o measurements/29.09-compressor/mine
$PY tools/harness/compare.py measurements/29.09-compressor/live measurements/29.09-compressor/mine \
    --cases measurements/29.09-compressor/compressor-threshold.built.json
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

## First run in Live 12.4.6 (2026-10-18)

Live 12.4.6 Trial with its bundled Max, macOS, 44.1 kHz.

- **Worked the first time:** pasting `clipboard.json` with **Edit > Paste**; Populate
  (`create_audio_track`, `insert_device` for all 42 effects); Dump (1065 parameters, every one
  with `default_value`, readable display text, `value_items` on all stepped ones, no stray quotes;
  the save dialog's `Macintosh HD:/Users/…` path was written to without change);
  `probePosition()` (the `this_device` path had the expected form); `duplicate_track`; setting
  values by `norm`; the export's delay compensation.
- **Fixed:** Build cases failed with `cannot read Macintosh HD:/…/compressor-threshold.json`.
  `readText` opened the file with the type list `"TEXT"`, and Max does not count a `.json` file as
  TEXT. It now opens with no type list. Test: "build reads a .json cases file from the open
  dialog's Max-style path"; the `File` mock now refuses a `.json` read with `"TEXT"`, as Max did.
- **Compressor, Threshold at 5 points** (`measurements/29.09-compressor/`): `bypass` and
  `default` equal the probe (impulse at 0 ms, 0 dB, sample offset 0). With the loaded preset
  (4:1, RMS, knee 6 dB, attack 1 ms, release 30 ms) the static curve fits an RMS detector (a sine
  reads 3 dB below its peak) and a 1/4 slope above the threshold: at Threshold −28.8 dB a −6 dBFS
  sine lost 14.85 dB. The Knee of 6 dB is a half-width: at all three finite thresholds below 0 dB
  the curve fits a quadratic soft knee over threshold ± 6 dB to within 0.01 dB
  (`live-12/audio-effects/29.09-compressor.md` › Measured).
- **Harness quirk:** on a silent render (a track with no clip) `analyse.py` still reports attack
  and release times (about 0.7 ms) from noise; ignore `dynamics` when `impulse.peak_db` is −240.
- **Before this run, checked without Live:** both test suites.

### Reverb run (`measurements/29.32-reverb/`, five sets, 2026-10-18)

Driven through desktop control (screenshots, clicks and keystrokes on the Live window), not by hand.
Later runs build the set as a file and open and check it through the Remote Script (2b), which
leaves only the export to the UI.

- **Size set through the API is ignored by the export while Smooth is Fast or Slow.** Five Size
  values gave bit-identical renders; with Smooth = None they differ, and a Fast case at Size 1.53
  equals the untouched default. Put `"Size Smoothing": {"item": "None"}` in every case that sets
  Room Size.
- **An export can come out early.** Three of the five Reverb exports were 1764 samples (40.00 ms)
  ahead of the probe, bypass included; the first two were exact. Cause not found (same steps, same
  devices). Check the `bypass` render's impulse position first (`impulse.taps[0].time_ms` is
  not enough: the impulse then lies before the window); fix with `analyse.py --align -1764`.
- **A save or open panel takes a path only through Go to Folder.** Typing `/Users/...` into a Save As
  name field turns the slashes into colons and saves a folder of that name on the Desktop. In the
  panel press Cmd+Shift+G, type the folder, Return, then type the bare name.
- **Dropping `probe.wav` warps it to about 63 BPM and shortens the clip**: turn Warp off after the
  drop (the clip then spans the whole file; its Start 1.1.1 and Length show in the status line
  when the clip is selected). Drop the file with the pointer at the very left of the lane or the
  clip lands on bar 2; Cut and Paste did not move it.
- **Export dialog:** the Render Length field keeps its last value; set it to the file's length in
  bars every run (60 for the 10 s gap, 150 for the 30 s gap). Settings other than Rendered Track
  and length persisted between runs.
- **The default set has four tracks and two returns that export as silent files**; delete them
  before building cases, and clear the browser's search box (it persists) before using Current
  Project.
- **Harness:** `impulse.rt60_s` reads far too short for a reverb with early reflections; refit from
  `.ir.wav`. `modulation` figures for a tone through a reverb are a rough spread, not a clean
  depth.
- A Build cases call on 20 to 24 cases took about 15 to 30 s; 60 bars rendered 24 tracks in under
  30 s, 150 bars in 40 s.

## Limits

- Attack and release shorter than one cycle of the 1 kHz tone (1 ms) read as about 0.5 ms.
- The sweep response assumes a time-invariant device; for modulated devices read `noise_db`.
- `build` finds a parameter by `name` or `original_name`; when two parameters of a device share
  a name, the first one wins.
- `--display` finds values by bisection and assumes the control's display is monotonic.
- `analyse.py`'s `rt60_s` and `noise_db` (186 ms window) do not suit reverbs, and its attack,
  release and FM figures failed for several devices in the top 100 runs; the device notes say
  where and give the figures computed from the renders instead.

### Generated set, Compressor (`measurements/29.09-compressor/compressor-gen.*`, 2026-10-18)

Live 12.4.6 opened both generated sets (`open -a`) with no warning or missing media.
Calibration mapped all 23 API parameters of the Compressor; two elements (`LegacyModel`,
`LegacyEnvFollowerMode`) move none. A set of three runs (the Threshold sweep, Attack by display
with Ratio and Model set, Release by norm with S/C EQ Freq, Knee and Output set; 20 tracks) read
back with every case value and every other parameter as intended. Threshold's stored values
match those Live saved for the probe-built run to within 1e-6. The Remote Script gives no
display text in 12.4.6 (`value_string` missing), so `map` reads the display from the dump.

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
