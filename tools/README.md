# Measurement tools

Tools that fill the `[measure]` gaps in the device notes (`../live-12/audio-effects/`) by
observing Live, and then check a new implementation of a device against what was measured. Two
parts:

| Part | What it does |
|---|---|
| [`probe-device/`](probe-device/) | **Suhina Probe**, a Max for Live audio effect. Passes audio through unchanged; dumps every device's parameters (range, default, steps, display text across the range, so tapers and units) to JSON; builds one track per test case with the device set to the case's values; adds a track per Live audio effect |
| [`harness/`](harness/) | Python: the probe signal (`signals.py`), case files from a dump (`cases.py`), measurements of renders (`analyse.py`), renders of the same set through the implementation under test (`render_set.py`), and the comparison (`compare.py`) |

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

## Limits

- Attack and release shorter than one cycle of the 1 kHz tone (1 ms) read as about 0.5 ms.
- The sweep response assumes a time-invariant device; for modulated devices read `noise_db`.
- `build` finds a parameter by `name` or `original_name`; when two parameters of a device share
  a name, the first one wins.
- `--display` finds values by bisection and assumes the control's display is monotonic.
