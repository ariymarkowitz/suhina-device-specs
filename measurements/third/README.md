# Third set: 147 runs on 39 devices (Live 12.4.7), in five parts and a pilot

The runs added to the devices' `runs.py` after the first three sets, 147 of them, to answer what the
first notes left open: the controls the harness could not move before (stored routing and mode
elements, automation lanes, MIDI and side-chain key tracks), curves at more frequencies and levels,
the aliasing switches, and the time behaviour of the modulation, fades and glides. `selection.json`
lists them; `third-1` to `third-5` hold them in five sets, and `../pilot/` holds six earlier runs that
tested the new mechanisms.

State: **built, opened in Live, verified, exported, analysed, and the answers written into the
device notes** (each note's Measured › Third set section; every run's plan step has a status line in
the note's Measurement plan).

| Part | Runs | Cases | Tracks | Probe |
|---|---|---|---|---|
| `third-1` | 31 | 251 | 230 | the 2 s probe |
| `third-2` | 28 | 275 | 254 | the 2 s probe |
| `third-3` | 22 | 128 | 120 | the 2 s probe |
| `third-4` | 32 | 270 | 237 | the extended probe (222 cases, `../probe-ext/`) and the 10 s probe (48, `../29.32-reverb/probe-gap10/`) |
| `third-5` | 34 | 234 | 207 | the extended probe |
| total | 147 | 1158 | 1048 | |

- `batch.py build measurements/third/selection.json` (per part): 1158 cases on 1048 tracks. Key tracks
  (`../probe-keys/`: a 1 kHz burst train, noise and a 110 Hz saw for the external side-chains) and MIDI
  tracks for the MIDI modes are part of the sets. `live_check.py verify`: all 1158 cases match
  (`third-N.verified.json`; stored elements are not read back by Live, so those cases verify
  the parameters only).
- Export: one render of selected tracks per part, 44.1 kHz WAV 32-bit, Normalize off, into `export/`
  (not in the repository): 1057 files, 24 GB (the tracks of the five parts, the key-signal tracks and
  the five full mixes `third-N.wav`).
- `batch.py analyse --trim` into the devices' `live/` (`third-N.analysis.json`).

## The pilot

`../pilot/` holds six runs (`autopan-waveform-lane`, `roar-single-routing`, `saturator-hiquality`,
`looper-state-lane`, `beatrepeat-grid-lane`, `utility-mute-lane`) that tried an automation lane, the
stored routing element and the stored oversampling element before the large sets were built. It
was rendered at 88.2 kHz and brought to 44.1 kHz; the Looper lane did not start the device there
(both cases are bit-identical to the bypass render), while the same lane in `third-1` at 44.1 kHz
does. The same six runs are in the third set and the notes read those renders.

## Live 12.4.7 against the `[measured 12.4.6]` tags

Live was updated to 12.4.7 on 2026-10-24 at 16:17. The top 100 set was exported before that and is
12.4.6. **The remaining set's renders were exported on 2026-10-24 at 22:32, after the update, so they
were made by 12.4.7, although its notes say `[measured 12.4.6]`.** Nothing was re-tagged; the tags of
those sections were left as they were. Where a 12.4.6 render and a 12.4.7 render of the same settings
could be compared they agree (the Resonators default echo at -19.2 dB, the Overdrive and Saturator curves at 1 kHz), and no gain or sound change
between the two versions was found. Everything in this set is tagged `[measured 12.4.7]`.

## Where the answers are

| Device (note's Measured section) | Runs | Run names |
|---|---|---|
| [Amp](../../live-12/audio-effects/29.01-amp.md#measured) | 5 | `amp-presence-models`, `amp-tone-interactions`, `amp-tone-stack-models`, `amp-gain-models`, `amp-volume-models` |
| [Auto Filter](../../live-12/audio-effects/29.02-auto-filter.md#measured) | 9 | `autofilter-morph-dj-comb`, `autofilter-clip-output-mix`, `autofilter-depth-up`, `autofilter-freq-res-grid`, `autofilter-lfo-params`, `autofilter-drive`, `autofilter-env-detector`, `autofilter-hiquality-alias`, `autofilter-resampling` |
| [Auto Pan-Tremolo](../../live-12/audio-effects/29.03-auto-pan-tremolo.md#measured) | 6 | `autopan-waveform-lane`, `autopan-waveforms-pan`, `autopan-random-width`, `autopan-sync-offset`, `autopan-harmonic-crossover`, `autopan-onset` |
| [Auto Shift](../../live-12/audio-effects/29.04-auto-shift.md#measured) | 5 | `autoshift-lfo-timing`, `autoshift-vibrato-natural`, `autoshift-glide`, `autoshift-ranges`, `autoshift-formant-saw` |
| [Beat Repeat](../../live-12/audio-effects/29.05-beat-repeat.md#measured) | 5 | `beatrepeat-grid-lane`, `beatrepeat-grid-midpoints`, `beatrepeat-chance-quarters`, `beatrepeat-variation-quarters`, `beatrepeat-interactions` |
| [Cabinet](../../live-12/audio-effects/29.06-cabinet.md#measured) | 1 | `cabinet-grid` |
| [Channel EQ](../../live-12/audio-effects/29.07-channel-eq.md#measured) | 2 | `channeleq-lanes`, `channeleq-alias-boost` |
| [Chorus-Ensemble](../../live-12/audio-effects/29.08-chorus-ensemble.md#measured) | 2 | `chorus-mode-switch`, `chorus-tap-phases` |
| [Compressor](../../live-12/audio-effects/29.09-compressor.md#measured) | 8 | `compressor-sidechain`, `compressor-drywet`, `compressor-log-lin-amounts`, `compressor-makeup-more`, `compressor-auto-release-bursts`, `compressor-rms-window`, `compressor-stereo`, `compressor-peak-buzz` |
| [Corpus](../../live-12/audio-effects/29.10-corpus.md#measured) | 7 | `corpus-midi`, `corpus-hit-listening`, `corpus-tune-types`, `corpus-drywet-ring`, `corpus-decay-radius`, `corpus-lfo`, `corpus-bleed-limiter` |
| [Delay](../../live-12/audio-effects/29.11-delay.md#measured) | 4 | `delay-freeze`, `delay-time-jump`, `delay-drywet-mode`, `delay-lfo-shapes` |
| [Drum Buss](../../live-12/audio-effects/29.12-drum-buss.md#measured) | 3 | `drumbuss-boom-freqs`, `drumbuss-curves-100hz`, `drumbuss-alias-stereo` |
| [Dynamic Tube](../../live-12/audio-effects/29.13-dynamic-tube.md#measured) | 3 | `dyntube-curves-100hz`, `dyntube-hiquality`, `dyntube-detector` |
| [Echo](../../live-12/audio-effects/29.14-echo.md#measured) | 4 | `echo-repitch-jump`, `echo-drywet-mode`, `echo-sync-more`, `echo-mod-shapes` |
| [EQ Eight](../../live-12/audio-effects/29.15-eq-eight.md#measured) | 4 | `eq-eight-freq-gain`, `eq-eight-freq-glide`, `eq-eight-oversampling`, `eq-eight-modes` |
| [EQ Three](../../live-12/audio-effects/29.16-eq-three.md#measured) | 2 | `eq-three-kill-lanes`, `eq-three-flat-element` |
| [External Audio Effect](../../live-12/audio-effects/29.18-external-audio-effect.md#measured) | 1 | `external-audio-effect-latency` |
| [Filter Delay](../../live-12/audio-effects/29.19-filter-delay.md#measured) | 1 | `filter-delay-time-jump` |
| [Gate](../../live-12/audio-effects/29.20-gate.md#measured) | 4 | `gate-sidechain`, `gate-detector-retrigger`, `gate-ramp`, `gate-stereo` |
| [Glue Compressor](../../live-12/audio-effects/29.21-glue-compressor.md#measured) | 4 | `glue-sidechain`, `glue-detector-release`, `glue-knee-ramp`, `glue-stereo-oversample` |
| [Grain Delay](../../live-12/audio-effects/29.22-grain-delay.md#measured) | 3 | `grain-delay-window`, `grain-delay-buttons`, `grain-delay-spray-train` |
| [Hybrid Reverb](../../live-12/audio-effects/29.23-hybrid-reverb.md#measured) | 5 | `hybrid-reverb-eq-ranges`, `hybrid-reverb-tides`, `hybrid-reverb-decay-algos`, `hybrid-reverb-freeze-toggle`, `hybrid-reverb-algo-controls` |
| [Limiter](../../live-12/audio-effects/29.24-limiter.md#measured) | 3 | `limiter-auto-release-bursts`, `limiter-link-routing`, `limiter-ceiling-modes` |
| [Looper](../../live-12/audio-effects/29.25-looper.md#measured) | 1 | `looper-state-lane` |
| [Multiband Dynamics](../../live-12/audio-effects/29.26-multiband-dynamics.md#measured) | 5 | `mbd-sidechain`, `mbd-solo-crossovers`, `mbd-amount-time-below`, `mbd-rms-window`, `mbd-knee-ramp` |
| [Overdrive](../../live-12/audio-effects/29.27-overdrive.md#measured) | 1 | `overdrive-curves-100hz` |
| [Pedal](../../live-12/audio-effects/29.28-pedal.md#measured) | 3 | `pedal-switching`, `pedal-curves-low-high`, `pedal-hiquality` |
| [Phaser-Flanger](../../live-12/audio-effects/29.29-phaser-flanger.md#measured) | 4 | `phaser-flanger-blend-amount`, `phaser-flanger-env-times`, `phaser-flanger-lfo2-sync`, `phaser-flanger-safe-warmth` |
| [Redux](../../live-12/audio-effects/29.30-redux.md#measured) | 4 | `redux-pre-corner`, `redux-rate-hq`, `redux-section-order`, `redux-bits-shape-ramp` |
| [Resonators](../../live-12/audio-effects/29.31-resonators.md#measured) | 3 | `resonators-others`, `resonators-gain-mix`, `resonators-notes-const` |
| [Reverb](../../live-12/audio-effects/29.32-reverb.md#measured) | 2 | `reverb-smooth-glide`, `reverb-freeze-toggle` |
| [Roar](../../live-12/audio-effects/29.33-roar.md#measured) | 6 | `roar-routings`, `roar-single-filters`, `roar-single-routing`, `roar-modulation`, `roar-single-shapers`, `roar-level-output-hq` |
| [Saturator](../../live-12/audio-effects/29.34-saturator.md#measured) | 6 | `saturator-color-more`, `saturator-curves-ramp`, `saturator-hiquality`, `saturator-hiquality-types`, `saturator-predc-step`, `saturator-waveshaper-more` |
| [Shifter](../../live-12/audio-effects/29.35-shifter.md#measured) | 4 | `shifter-midi`, `shifter-freq-wide`, `shifter-lfo-more`, `shifter-window-more` |
| [Spectral Resonator](../../live-12/audio-effects/29.36-spectral-resonator.md#measured) | 4 | `spectral-resonator-midi-mono`, `spectral-resonator-midi-poly`, `spectral-resonator-modulation`, `spectral-resonator-long-decay-unison` |
| [Spectral Time](../../live-12/audio-effects/29.37-spectral-time.md#measured) | 3 | `spectral-time-freeze-lane`, `spectral-time-resolution-order`, `spectral-time-synced-steps` |
| [Utility](../../live-12/audio-effects/29.40-utility.md#measured) | 3 | `utility-mute-lane`, `utility-midside`, `utility-dc-audition` |
| [Vinyl Distortion](../../live-12/audio-effects/29.41-vinyl-distortion.md#measured) | 2 | `vinyl-distortion-crackle-repeat`, `vinyl-distortion-band` |
| [Vocoder](../../live-12/audio-effects/29.42-vocoder.md#measured) | 5 | `vocoder-band-counts`, `vocoder-carriers`, `vocoder-enhance-saw`, `vocoder-pitch-tracking`, `vocoder-gate-ramp` |

The analyses are in each device's `live/` and, for all runs, in `third-N.analysis.json`. Most answers
needed more than `analyse.py` gives; the notes say how each figure was read (Hilbert envelopes and
autocorrelation for periods, cross-correlation for delay and lag, comb or partial scores for pitches,
offline models of a hard clip and of resamplers for aliasing, Schroeder curves, tap lists, fits of
sines and pulses to modulation traces).

## What the set showed across devices

- **Stored elements reach the audio**, which the first sets could not rely on: Roar's routing
  (`Input_RoutingMode`, seven modes in the Max wrapper's order), the oversampling switches of Saturator,
  Pedal and Roar, Spectral Time's Resolution, Zero Dry Signal Latency and order,
  the Vocoder's carrier source, and the MIDI pitch mode with its routing in Shifter, Spectral Resonator
  and Corpus. `Spectral Resonator`'s frequency dial mode and the Vocoder's band count are stored but were not
  separated from their defaults by these renders (read in the fourth set).
- **Automation lanes work at 44.1 kHz**: the Looper's State, Utility's Mute and Gain, Reverb's Freeze,
  Hybrid Reverb's and Spectral Time's freeze, Delay and Echo time jumps, EQ and Chorus switches. Mute is
  a hard sample-accurate switch; Gain ramps over about 4 ms.
- **Oversampling when Hi-Quality is on**: Saturator is 4x (the alias lines of a hard clip match an offline
  4x model to 0.1 dB); Pedal and Roar lower the strongest alias by 11 to 32 dB, and their impulse responses
  show pre-ringing of 5 to 50 samples, i.e. a delay-compensated
  latency whose size the export hides. Overdrive and Vinyl Distortion alias with no oversampling.
- **LFO phase is tied to the song position**: Phaser-Flanger's LFOs are `-sin(2 pi f t)` in the delay
  exponent with `t` from the start of the song, at free and synced rates (Rate list entries are bar
  fractions); Roar's LFO 1 has an offset of 0.14 cycle.
- **Two-section DC filters**: Saturator's Pre-DC Filter is two one-pole high-passes at 27 Hz and
  Utility's DC Filter two at 5 Hz, replacing the one-pole readings of 12.4.6.
- **Dry/Wet and Delay modes**: Delay's and Echo's stored `DryWetMode` selects linear or equal-loudness;
  the laws in [`common.md`](../../live-12/audio-effects/common.md#drywet) were updated.
- **Hysteresis and thresholds**: Vocoder's Gate opens at -39.75 dBFS and closes at -40.75 for a tone
  in one band at -30 dB; Compressor's loaded preset has its side-chain EQ on with an 80 Hz high-pass,
  which explains its 50 Hz and low sweep behaviour; Limiter's Link is a linear amplitude blend of the two
  channels' reduction.
- **Findings against the manual or the first notes**: Spectral Time's longest delay is capped near 5.9 s;
  Overdrive's Amount 0 and Roar's Amount 0 are not bypasses; Roar's Morph runs LP, BP, HP, Notch, LP;
  Pedal's Fuzz has no gate; Utility's Mid/Side knob is two linear gains, one always unity; Shifter's Spin
  and Offset did nothing in Pitch mode; Vinyl Distortion's Tracing goes chaotic with the band far from a
  high tone at Drive 1.

## Settings that did not read, and what is open

- **Looper**: the Overdub pass leaves the first take at 0.42 and the playback is 0.95 of the input; the
  Feedback law and the crossfades need a noise take and a click track.
- **Delay and Filter Delay**: the splice at a time jump with a periodic test tone was hidden (a 1 kHz
  tone over a 100 ms shift). Delay's `delay-time-jump-noise` (fourth set) found a lane's step sample-exact
  and the same in Repitch, Fade and Jump, so the modes need a ramped lane (candidate
  `delay-time-ramp-noise`); Filter Delay's Fade and Jump modes are not run.
- **Glue Compressor** Oversample did not clip in the test; **Limiter** fs/4 at 45 degrees is open;
  **Corpus** Tune sharpness and Random and LFO details are open.
- **Compressor** 50 Hz buzz: the `compressor-peak-buzz` render had the preset's side-chain EQ on;
  `compressor-peak-buzz-eq-off` (fourth set) repeats it with the EQ off: 21.7 % THD at the fastest times.
- **Phaser-Flanger** envelope times: Env Amount +1 clamped the delay at its shortest for the bed and
  the burst, so no time constant was fitted; `phaser-flanger-env-times-small` (fourth set) fits Release
  (a pole of about the setting) and Attack 30 ms.
- **Spectral Resonator**: Mod Rate was changed only with ModMode None, and the frequency dial mode case had
  equal values in both dials; the fourth set read both (Mod Rate speeds Chorus and Wander up; mode 0 is
  Hertz, 1 is the note). Mod Rate in Granular and in Hz is open.
- **Spectral Time**: ProcessingOrder was rendered at 1 only; the fourth set has both orders.
  AvoidFreezingOnsets without a reference is open.
- **Vocoder**: the band counts were at Filter Width 100 % where the bands tile; the fourth set counted them
  at 25 % (stored 0 to 7 give 4 to 32 bands in steps of 4) and moved the Pitch Tracking limits (the rule
  for a parked oscillator is open).
- **Not set up**: Shifter's Spread, Roar's other matrix cells, Pedal's 20 Hz staircase.

The eight candidate runs of this list were run as the fourth set
([`../fourth/README.md`](../fourth/README.md)).
