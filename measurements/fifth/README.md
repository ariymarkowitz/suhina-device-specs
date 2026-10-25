# Fifth set: every item the third and fourth sets left open (Live 12.4.7)

The runs added to the devices' `runs.py` for what the notes still listed as open after the fourth set:
[`../third/README.md`](../third/README.md) › Settings that did not read, and what is open, and
[`../fourth/README.md`](../fourth/README.md) › Left open, plus the Looper's Speed and Reverse, which a State
lane now makes measurable. `selection.json` lists them; `fifth.als` is the set. A sixteenth run, the
Shifter's Wide and Spread (`shifter-wide-spread`), was added after the user saw that the Fine dial becomes
Spread when Wide is on: it is its own small set in [`../fifth-wide/`](../fifth-wide/selection.json).

State: **built, opened in Live, verified, exported, analysed, and the answers written into the
twelve device notes** (each note's Measured › Fifth set).

| Run | Device | Cases | Probe | Answer (note) |
|---|---|---|---|---|
| `looper-feedback-noise` | Looper | 12 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.25-looper.md#fifth-set-live-1247) |
| `looper-speed-reverse` | Looper | 10 | 2 s | the same |
| `delay-time-ramp-noise` | Delay | 5 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.11-delay.md#fifth-set-live-1247) |
| `filter-delay-time-step-noise` | Filter Delay | 5 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.19-filter-delay.md#fifth-set-live-1247) |
| `filter-delay-time-ramp-noise` | Filter Delay | 5 | 2 s | the same |
| `glue-oversample-clip` | Glue Compressor | 6 | extended | [Measured › Fifth set](../../live-12/audio-effects/29.21-glue-compressor.md#fifth-set-live-1247) |
| `limiter-fs4-45` | Limiter | 5 | fifth | [Measured › Fifth set](../../live-12/audio-effects/29.24-limiter.md#fifth-set-live-1247) |
| `corpus-tune-sweep` | Corpus | 22 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.10-corpus.md#fifth-set-live-1247) |
| `corpus-lfo-steady` | Corpus | 18 | 2 s | the same |
| `vocoder-pitch-rest` | Vocoder | 5 | fifth | [Measured › Fifth set](../../live-12/audio-effects/29.42-vocoder.md#fifth-set-live-1247) |
| `spectral-resonator-mod-rate-tone` | Spectral Resonator | 17 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.36-spectral-resonator.md#fifth-set-live-1247) |
| `spectral-time-avoid-onsets` | Spectral Time | 8 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.37-spectral-time.md#fifth-set-live-1247) |
| `shifter-spin-sync` | Shifter | 11 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.35-shifter.md#fifth-set-live-1247) |
| `roar-matrix-targets` | Roar | 22 | 2 s | [Measured › Fifth set](../../live-12/audio-effects/29.33-roar.md#fifth-set-live-1247) |
| `pedal-low-high-stairs` | Pedal | 11 | fifth | [Measured › Fifth set](../../live-12/audio-effects/29.28-pedal.md#fifth-set-live-1247) |
| `shifter-wide-spread` (`../fifth-wide/`) | Shifter | 13 | 2 s | the Shifter's Fifth set |

("2 s" is the main probe `measurements/probe.wav`, 46.75 s; "extended" is `measurements/probe-ext/`, 86.5 s;
"fifth" is the new `measurements/probe-fifth/`, 42.25 s.)

- **The new probe** (`tools/harness/signals.py --kind fifth`, `measurements/probe-fifth/probe.json`; the WAV is
  made again by `python tools/harness/signals.py --kind fifth --rate 44100 --gap 1 -o measurements/probe-fifth/probe.wav`):
  an impulse, two sines at a quarter of the sample rate at 0 and 45 degrees (-6 dBFS), a 20 Hz staircase
  (-54 to -6 dBFS in 3 dB steps of 0.5 s), a 5 kHz staircase (the same in steps of 0.25 s), an 18 s
  sequence of saws and sines with silences between them (`vocseq`: 220, 1760, 330, 1760, 1760, 40, 110, 40,
  3000 sine, 150, 3000 sine, with rests between most of them) and silence.
- `batch.py build measurements/fifth/selection.json`: 15 runs, 162 cases on 151 tracks. `live_check.py verify`:
  all 162 cases match, 0 problems (`fifth.verified.json`; five Corpus `sync-*` cases are reported without a
  display text for the stored sync index, which is only how Live shows it). The Wide set:
  13 cases on 13 tracks, verified with 0 problems (`../fifth-wide/fifth-wide.verified.json`).
- Export: all tracks of `fifth.als` at once under the name `fifth` (the longest probe's length), 44.1 kHz WAV
  32-bit, Normalize off, into `export/` (not in the repository). The user exported `fifth-wide.als` into the
  same `export/` folder under `fifth-wide`, 24 bars.
- `batch.py analyse --trim` into the devices' `live/` (`fifth.analysis.json` and
  `../fifth-wide/fifth-wide.analysis.json`: the export's offset against each probe is 0 samples in every
  group). `analysis` reads only the fields it knows for the older probes, so the figures in the notes come
  from the raw renders with one-off scripts (not kept in the repository): least-squares fits of a looped
  output on the earlier passes of the input noise (Looper), lag matching of low-passed signals (Delay,
  Filter Delay), spectra of 32768-sample windows (Glue Compressor, Shifter, Corpus, Spectral Resonator),
  autocorrelation (Vocoder), DFTs at the tone over whole cycles (Pedal, Roar, Limiter). Their definitions are
  in the notes' paragraphs.

## What the runs showed

- **Looper**: Feedback is a plain gain on the old layer, once per Overdub pass (75 % gives 0.563 and 0.750 of
  the two older layers, 50 % 0.25 and 0.50), and a Feedback lane acts at the sample, not at the next
  repetition. Every write of the loop (the recording and each Overdub pass) passes through a fixed
  zero-phase low-pass: flat to 10 kHz, 0.94 at 16 kHz, 0.79 at 20 kHz, centre tap 0.950, which is the 0.95
  of the third set; the 0.42 of that set is most probably the Overdub to Play crossfade (about 5 ms) falling
  on the impulse. The loop's end fades out over 4 to 5 ms; the start does not fade in. Speed is in
  semitones, 2^(Speed / 12) with no level change; Reverse plays the loop backwards from the Play change.
- **Delay**: the lane's ramp of L Time is exponential (100 ms times 2 to the fraction), Fade and Jump follow
  it without lag in steps about 40 ms apart, and Repitch glides with a lag of about 0.15 s (a one-pole of
  that time constant) and plays the echo up to 4.4 % slow.
- **Filter Delay**: the stored `DelayTransitionMode` 0 glides (tau about 0.16 s), 1 (the loaded value)
  crossfades over about 25 ms starting 10 ms late, 2 jumps at the sample; its lane's ramp is linear in
  milliseconds, unlike the Delay's.
- **Glue Compressor**: Oversample is a 2x oversampling of the clipper: the aliases that fold at 44.1 kHz fall
  by 40 to 55 dB or more, those that fold at 88.2 kHz stay.
- **Limiter**: Standard limits the sample peaks (fs/4 at 45 degrees stays 1 dB over the ceiling between
  samples), True Peak the reconstructed ones, Soft Clip is in between and acts on the sample values.
- **Corpus**: the audio is sharp of Tune by a smooth 9 to 35 cents (peak between 196 and 330 Hz), exact only
  at the default, and independent of Decay, Quality and Brightness. The LFO Rate is in Hz (0.5 to 10), the
  sync steps 6 and 12 are as listed but step 17 runs at half the listed rate, Phase and Spin act on the
  right LFO (Spin multiplies its rate by 1 + Spin) and Offset shifts a synced LFO.
- **Vocoder**: at the loaded limits the oscillator keeps its last tracked pitch (to 4 %) through silences
  and out-of-range tones; at 200 to 800 Hz and for a tone at the Upper limit it does not follow that rule.
- **Spectral Resonator**: in Chorus the partial's level fluctuates at Mod Rate / 3 Hz whatever the Pitch Mod;
  Wander is about a third of that; Granular plays about 0.28 grains per second per percent at low rates.
- **Spectral Time**: AvoidFreezingOnsets lets the onset pass before it freezes, so the held sound is the
  sustained one and an impulse is not captured.
- **Shifter**: with Wide on the Fine knob is Spread: left Coarse + Fine, right Coarse - Fine, in cents and in
  Hz, in all three modes. Spin still does nothing; Offset shifts a synced LFO, Phase is right minus left.
- **Roar**: Input, Dry/Wet, Stage 1 Amount, Trim and Frequency respond to a matrix cell; Global Mod Amt scales
  every cell linearly. Blend (not in Single), Feedback Amount (the user sees it act in Single) and the
  filter Morph (left at 0, where both ends are Low Pass) gave nothing, which is a flaw of the cases, not a
  finding.
- **Pedal**: at 20 Hz each circuit is linear below its knee and its gain is far under the 1 kHz one; at 5 kHz
  Distortion and Fuzz at Gain 100 % are saturated from the first step.

## Left open

- **Looper**: the partner of the end-of-loop fade, the fade at the start of a recording, Reverse on
  layered loops, whether the write low-pass scales with the sample rate, Undo and the other states.
- **Delay and Filter Delay**: the crossfade length in Delay's Fade and Hi-Quality off or Eco on a ramp.
- **Glue Compressor**: the oversampling's delay in samples and 48 kHz.
- **Corpus**: why only the default Tune is exact (Tune values near 261.63 Hz, 250 and 275, would show
  whether the curve falls to zero just there), the range ends of LFO Rate, the other sync steps (17 against
  its listed value), Duty Cycle and the sign of the Phase and Offset shifts.
- **Vocoder**: the rule at 200 to 800 Hz and at the Upper limit, and the tracker's latency.
- **Spectral Resonator**: the grain envelope and Pitch Mod 2 and 4 st in each mode.
- **Shifter**: Width. Spin does nothing in the render and in the user's hands in Live 12.4.7, so it is
  probably a bug there.
- **Roar**: Feedback Amount and the filter Morph again (Morph knob in the middle, Feedback Amount at 50 %),
  Blend in a two-stage routing, cells below 1, negative cells and the other stages' targets.
- **Pedal**: Gain 25 and 75 % and 10 dB steps at the two frequencies.
- the points listed in [`../third/README.md`](../third/README.md) › Settings that did not read, and what is
  open, that are not named above.
