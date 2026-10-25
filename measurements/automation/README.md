# Automation runs (Live 12.4.6)

What these show is written up in [`live-12/automation.md`](../../live-12/automation.md), and
Utility's own part in its note. Unlike the device runs, these sets were made by hand in Live (the
Remote Script cannot draw automation), so each set here is the one the render came from.

Every set has a MIDI track with Operator playing a long C3 (a sine, 261.6 Hz) at 120 BPM and one
automation lane on it: straight segments, bent segments and, from the second Utility run on,
a jump (two points at one beat).

| Run | Automates | What it is for | Render |
|---|---|---|---|
| `utility-gain-curves` | Utility's Gain | straight segments across the knob's range, the two extreme bends, two medium ones | Bounce to New Track, 44.1 kHz |
| `utility-gain-jump13` | Utility's Gain | the same, with a jump at beat 28 from -9.4 to +3.7 dB | Bounce, 44.1 kHz |
| `utility-gain-jump62` | Utility's Gain | a jump at beat 28 from -54.7 to +7.8 dB (gain or dB) | Bounce, 44.1 kHz |
| `utility-gain-jump62-88k` | Utility's Gain | the same set at 88.2 kHz (a fixed time or a fixed number of samples) | Bounce, 88.2 kHz |
| `track-volume` | the track's Volume | the whole fader from the bottom to the top, bends both ways, a jump at beat 30 | recorded post-mixer on a second track, 24-bit, 44.1 kHz |
| `operator-volume-88k` | Operator's Volume | the Utility run's shape on another gain parameter, a jump at beat 28 | Bounce, 88.2 kHz |
| `operator-fine` | Operator A's Fine (ratio mode) | a pitch parameter over 4 beats, bends, jumps at beats 2 and 3 | Bounce, 44.1 kHz |
| `utility-gain-splits` | Utility's Gain | eight bent segments (bars 1 to 4), the same split by a point each (bars 5 to 8), split segments reshaped by hand (bar 9) | Bounce, 88.2 kHz |
| `curve-drag` | Utility's Gain | 14 starting curves in 4 copies, each copy Alt-dragged by hand by a different amount | Bounce, 88.2 kHz |
| `curve-drag-lopsided` | Utility's Gain | 12 lopsided S curves and curves that cross the diagonal in 4 copies; copy 4 dragged twice the same way | Bounce, 88.2 kHz |

`kinds/` holds a different sort of run: lanes on an integer, a frequency, a choice and a toggle,
built as files by `make_als.py build` (a point may carry the Bezier controls of the segment that
starts at it), read by moving the playhead to each beat of a grid with playback stopped and asking
the Remote Script for the parameter (`poll.py`), and compared by `analyse.py`. No render is made.

| Set | Lanes | Poll |
|---|---|---|
| `kinds/kinds.als` (from `resonators.json`, `eq-eight.json`, `auto-pan.json`) | Resonators I Note (straight, two bends, three short ones), I On (up, down); EQ Eight 3 Frequency A (straight, two bends); Auto Pan Waveform (three) | `live/kinds.poll.json`, 273 beats of 0.125, about 15 minutes |
| `kinds/kinds-negative.als` (from `corpus.json`) | Corpus Transpose 3 to -3 and back over 12 beats | `live/kinds-negative.poll.json` |

A Bounce renders the track before its mixer, so the track volume run was recorded instead: the
Operator track routed into a second audio track's input and recorded there.

The two drag sets started as files: `curve_drag.py make` writes them from
`sets/utility-gain-splits.als` with the starting curves listed in the script, and the curves were
then dragged in Live and the set saved. Each copy is one segment per bar alternating 0 dB and
+12 dB, then a flat bar. To drag the curves again, make the starting sets and follow the plan in
the script's docstring (copy 1 a little one way, copy 2 a lot the same way, copy 3 the other
way, copy 4 the same way as copy 2).

## Files

- `sets/<run>.als`: the set (the automation is the first track's first envelope).
- `export/<run>.wav`: the render, not in the repository (`export/` is ignored). They were saved
  by Live under `Samples/Processed/Bounce/` (and `Samples/Recorded/` for track-volume) of the
  Project the sets came from; to make them again, open the set in Live 12 and Bounce the first
  track (Arrangement, the whole song), or for track-volume record its second track.
- `analyse.py`: reads each set and its render and writes `live/<run>.json` (the points, the
  error of each reading per segment, the ramp fits at the jumps) and `live/<run>.envelope.csv`
  (level in dBFS, or frequency in Hz, every 2 ms). It also writes `live/fader-taper.csv` from
  the track volume run. Run it with `tools/.venv/bin/python measurements/automation/analyse.py
  [run ...]` (numpy only; a few minutes for all ten).
- `curve_drag.py`: `analyse` checks every split in `utility-gain-splits` against de Casteljau and
  replays every drag of the two drag sets through the rule in automation.md › Dragging a curve,
  writing `live/utility-gain-splits.splits.json` and `live/<run>.drags.json` (each segment's
  starting and saved curve, its paths and the fitted steps); `make` writes the starting sets.
  It reads the sets only, no renders.
