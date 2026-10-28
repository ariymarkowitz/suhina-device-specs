# Devices

One folder per device of Live 12, named like its note in `live-12/`: `29.NN-name` for the audio
effects (`live-12/audio-effects/`), `30.NN-name` for the MIDI effects (`live-12/midi-effects/`).

```
devices/29.01-amp/
  runs.py      the device's measurement runs: what to set, what it answers (kept)
  cases/       one file per run: every case's settings, written by `measure.py build` (kept)
  results/     Live's measured response to each case, one JSON per rendered track (kept)
  renders/     Live's exported audio of each case          (not in the repository)
  extras/      CSV views and impulse responses of results (not in the repository)
```

**What to build a device from** is `results/`: for a run `amp-gain` and a case `gain-10`,
`results/amp-gain gain-10.json` holds what `analyse.py` measured from Live's render of that case
(impulse taps and decay time, frequency response, static gain curve with distortion, attack and
release, modulation, stereo matrix, output with no input; the keys are listed in
`tools/harness/analyse.py`), and `cases/amp-gain.json` says which parameter values the case set.
`bypass` and `default` are in every run. The device's note says what each run showed.
Several runs can share a track (the `bypass` of a device, a `default` another run also has): the
result is then under the first run that had it, and `cases/` names the track
(`measure.py summary <device>` follows it).

MIDI effects have no audio: `results/<run>.json` holds each case's input and output notes
(`tools/harness/midi_set.py`).

**To measure again**, see the top-level README › Measuring a device yourself. To see a device's
runs: `tools/.venv/bin/python tools/harness/measure.py list amp`.
