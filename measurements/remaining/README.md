# Remaining priority 1 to 3 runs (Live 12.4.6), in one set

The 157 runs of the devices' `runs.py` files that the top 100 (`../top100/`) did not take: 25 of
priority 1, 100 of priority 2 and 32 of priority 3. `selection.json` lists them, priority first.

State: **built, opened in Live, verified, exported, analysed, and the answers written into the
device notes** (each note's Measured section, or the Behaviour section of Compressor's note, which
has none; every run's plan step has a status line in the note's Measurement plan).

- Export: two renders of selected tracks, 44.1 kHz WAV 32-bit, Normalize off: tracks 1 to 926
  (2 s probe) as `remaining` at 24 bars, the last 41 (10 s probe) as `remaining-gap10` at 60 bars,
  967 files, 16 GB, into `export/` (not in the repository). Live named one file
  `remaining autopan-attack attack-0.5-1.wav`; it was renamed to `... attack-0.5.wav`.
- `batch.py analyse --trim`: offset 0 samples from all 44 bypass renders; 967 renders analysed
  into the devices' `live/` (`remaining.analysis.json`). 54 cases have no impulse in the render
  (closed gates, Beat Repeat idling, Volume 0, Amp Volume 0 and the like); none is silent
  throughout.

- `batch.py build measurements/remaining/selection.json`: 1134 cases on 967 tracks (151 runs on
  the 2 s probe, 6 on the 10 s probe). `remaining.als`, `remaining.cases.json`.
- `live_check.py verify`: 1133 of 1134 cases match (`remaining.verified.json`). The other,
  `shifter-envelope default`, sets Env Amount to 0 st: stored as asked, and Live reads API 0.5
  where the harness took 0.46875, the other end of the flat 0.00 st stretch of the display.
- Two harness faults showed up while building and were fixed (`tools/harness/make_als.py`, with
  tests): a display at the very end of a control's range (Delay Feedback 95 %) was refused as
  outside it by a float32 rounding, and five parameters whose display is a tapered curve (Redux
  Jitter, Roar Feedback, Auto Filter LFO Amount, Chorus Warmth, Hybrid Reverb Algo Delay) were
  mapped as storing the API value when the element stores the displayed number. Before the fix
  Algo Delay 100 ms came out as 501 ms. `measurements/als-map-12.4.6.json` has the five corrected.

## Where the answers are

| Device (note's Measured section) | Runs | Run names |
|---|---|---|
| [Amp](../../live-12/audio-effects/29.01-amp.md#measured) | 3 | `amp-volume`, `amp-presence`, `amp-dual-mono` |
| [Auto Filter](../../live-12/audio-effects/29.02-auto-filter.md#measured) | 3 | `autofilter-types-other`, `autofilter-lfo-waves`, `autofilter-lfo-amount` |
| [Auto Pan-Tremolo](../../live-12/audio-effects/29.03-auto-pan-tremolo.md#measured) | 6 | `autopan-shape`, `autopan-stereo-offset`, `autopan-time-modes`, `autopan-attack`, `autopan-dynmod`, `autopan-harmonic-vintage` |
| [Auto Shift](../../live-12/audio-effects/29.04-auto-shift.md#measured) | 7 | `autoshift-strength`, `autoshift-vibrato`, `autoshift-lfo-waves`, `autoshift-lfo-depth`, `autoshift-scale`, `autoshift-formant`, `autoshift-gain-mix` |
| [Beat Repeat](../../live-12/audio-effects/29.05-beat-repeat.md#measured) | 6 | `beatrepeat-trigger`, `beatrepeat-decay-volume`, `beatrepeat-pitch`, `beatrepeat-filter`, `beatrepeat-mix-modes`, `beatrepeat-variation` |
| [Cabinet](../../live-12/audio-effects/29.06-cabinet.md#measured) | 5 | `cabinet-mic`, `cabinet-product`, `cabinet-linearity`, `cabinet-dual-mono`, `cabinet-drywet` |
| [Channel EQ](../../live-12/audio-effects/29.07-channel-eq.md#measured) | 2 | `channeleq-highpass`, `channeleq-combined` |
| [Chorus-Ensemble](../../live-12/audio-effects/29.08-chorus-ensemble.md#measured) | 6 | `chorus-auto-amount`, `chorus-vibrato-shape`, `chorus-width`, `chorus-feedback`, `chorus-highpass-warmth`, `chorus-mix-output` |
| [Compressor](../../live-12/audio-effects/29.09-compressor.md#behaviour) | 3 | `compressor-env-mode`, `compressor-lookahead`, `compressor-makeup` |
| [Corpus](../../live-12/audio-effects/29.10-corpus.md#measured) | 6 | `corpus-decay-material`, `corpus-tune-spread`, `corpus-hit-inharm`, `corpus-type-params`, `corpus-quality-width`, `corpus-filter-bleed` |
| [Delay](../../live-12/audio-effects/29.11-delay.md#measured) | 7 | `delay-offset`, `delay-lfo-delay`, `delay-lfo-filter`, `delay-lfo-waves`, `delay-time`, `delay-pingpong`, `delay-drywet` |
| [Drum Buss](../../live-12/audio-effects/29.12-drum-buss.md#measured) | 4 | `drumbuss-boom`, `drumbuss-transients`, `drumbuss-damp-crunch`, `drumbuss-mix-output` |
| [Dynamic Tube](../../live-12/audio-effects/29.13-dynamic-tube.md#measured) | 4 | `dyntube-tone`, `dyntube-envelope`, `dyntube-env-time`, `dyntube-output-wet` |
| [Echo](../../live-12/audio-effects/29.14-echo.md#measured) | 8 | `echo-time-offset`, `echo-gate-duck`, `echo-mod-delay`, `echo-mod-filter-env`, `echo-reverb`, `echo-channel-stereo`, `echo-noise-wobble`, `echo-input-mix` |
| [EQ Eight](../../live-12/audio-effects/29.15-eq-eight.md#measured) | 3 | `eq-eight-scale`, `eq-eight-shelf-q`, `eq-eight-freq` |
| [EQ Three](../../live-12/audio-effects/29.16-eq-three.md#measured) | 1 | `eq-three-freq` |
| [Erosion](../../live-12/audio-effects/29.17-erosion.md#measured) | 3 | `erosion-noise`, `erosion-blend`, `erosion-stereo` |
| [External Audio Effect](../../live-12/audio-effects/29.18-external-audio-effect.md#measured) | 1 | `external-audio-effect-unrouted-mix` |
| [Filter Delay](../../live-12/audio-effects/29.19-filter-delay.md#measured) | 3 | `filter-delay-pan`, `filter-delay-levels`, `filter-delay-routing` |
| [Gate](../../live-12/audio-effects/29.20-gate.md#measured) | 4 | `gate-return`, `gate-hold`, `gate-lookahead`, `gate-flip` |
| [Glue Compressor](../../live-12/audio-effects/29.21-glue-compressor.md#measured) | 4 | `glue-range`, `glue-attack-amount`, `glue-softclip`, `glue-makeup-mix` |
| [Grain Delay](../../live-12/audio-effects/29.22-grain-delay.md#measured) | 4 | `grain-delay-feedback`, `grain-delay-spray`, `grain-delay-random`, `grain-delay-stereo-mix` |
| [Hybrid Reverb](../../live-12/audio-effects/29.23-hybrid-reverb.md#measured) | 7 | `hybrid-reverb-predelay`, `hybrid-reverb-output`, `hybrid-reverb-eq`, `hybrid-reverb-blend`, `hybrid-reverb-darkhall`, `hybrid-reverb-shimmer`, `hybrid-reverb-freeze` |
| [Limiter](../../live-12/audio-effects/29.24-limiter.md#measured) | 1 | `limiter-lookahead-modes` |
| [Looper](../../live-12/audio-effects/29.25-looper.md#measured) | 1 | `looper-monitor-states` |
| [Multiband Dynamics](../../live-12/audio-effects/29.26-multiband-dynamics.md#measured) | 1 | `multiband-dynamics-bands` |
| [Overdrive](../../live-12/audio-effects/29.27-overdrive.md#measured) | 2 | `overdrive-dynamics`, `overdrive-drywet` |
| [Pedal](../../live-12/audio-effects/29.28-pedal.md#measured) | 3 | `pedal-eq-mid`, `pedal-eq-bass-treble`, `pedal-output-mix` |
| [Phaser-Flanger](../../live-12/audio-effects/29.29-phaser-flanger.md#measured) | 4 | `phaser-flanger-lfo-shape`, `phaser-flanger-lfo-stereo`, `phaser-flanger-envelope`, `phaser-flanger-warmth-output` |
| [Redux](../../live-12/audio-effects/29.30-redux.md#measured) | 3 | `redux-shape-dc`, `redux-jitter`, `redux-drywet` |
| [Resonators](../../live-12/audio-effects/29.31-resonators.md#measured) | 3 | `resonators-color`, `resonators-filter`, `resonators-routing` |
| [Reverb](../../live-12/audio-effects/29.32-reverb.md#measured) | 6 | `reverb-locut-law`, `reverb-smooth-slow`, `reverb-spin-grid`, `reverb-diffusion-size10`, `reverb-network-freq`, `reverb-freeze-static` |
| [Roar](../../live-12/audio-effects/29.33-roar.md#measured) | 5 | `roar-tone`, `roar-feedback`, `roar-filter-res`, `roar-compressor-output`, `roar-shaper-types-b` |
| [Saturator](../../live-12/audio-effects/29.34-saturator.md#measured) | 4 | `saturator-waveshaper`, `saturator-bass-shaper`, `saturator-postclip`, `saturator-predc` |
| [Shifter](../../live-12/audio-effects/29.35-shifter.md#measured) | 5 | `shifter-ring`, `shifter-delay-loop`, `shifter-pitch-window`, `shifter-lfo`, `shifter-envelope` |
| [Spectral Resonator](../../live-12/audio-effects/29.36-spectral-resonator.md#measured) | 3 | `spectral-resonator-damp-harmonics`, `spectral-resonator-shift-unison`, `spectral-resonator-send-mix-latency` |
| [Spectral Time](../../live-12/audio-effects/29.37-spectral-time.md#measured) | 6 | `spectral-time-freeze-sync`, `spectral-time-delay-shift`, `spectral-time-tilt-spray`, `spectral-time-freeze-onsets`, `spectral-time-delay-feedback`, `spectral-time-mix-latency` |
| [Spectrum](../../live-12/audio-effects/29.38-spectrum.md#measured) | 1 | `spectrum-transparency` |
| [Tuner](../../live-12/audio-effects/29.39-tuner.md#measured) | 1 | `tuner-transparency` |
| [Utility](../../live-12/audio-effects/29.40-utility.md#measured) | 3 | `utility-channels-order`, `utility-balance`, `utility-dc` |
| [Vinyl Distortion](../../live-12/audio-effects/29.41-vinyl-distortion.md#measured) | 2 | `vinyl-distortion-crackle`, `vinyl-distortion-global-drive` |
| [Vocoder](../../live-12/audio-effects/29.42-vocoder.md#measured) | 3 | `vocoder-formant`, `vocoder-unvoiced`, `vocoder-output-modes` |

The analyses are in each device's `live/` and, for all runs, in `remaining.analysis.json`. Many
answers need more than `analyse.py` gives (it was built for static curves and impulses): the notes
say how each figure was read (Hilbert envelopes and instantaneous frequency for delay swings,
cross-correlation against the probe's noise for delay tracking, spectral lines for partials and
sidebands, Schroeder curves per band for reverbs, impulse taps for mix laws, a fit of the staircase
to a transfer curve for shapers).

## What the set showed across devices

- **Dry/Wet has several laws** (linear, equal-power, an S-shaped power-complementary one, a raised
  cosine, and Corpus's own); the dry part is never delayed. The families and the devices in each are
  in [`common.md`](../../live-12/audio-effects/common.md#drywet), replacing the earlier "linear unless
  noted" guess.
- **Output acts on the wet signal only** in Drum Buss and Echo, so the dry path at Dry/Wet below
  100 % is not scaled by it.
- **Butterworth responses fit** Corpus's filter pair, Utility's Bass Mono (third order, top 100) and
  Redux's Post filter (order 16, top 100); Phaser-Flanger's delay follows an exponent that is linear
  in the LFO, with the Flanger's swing growing in the Amount.
- **Some modulation depths are fits to few points**: the cubic law of Delay's LFO > Delay (shared by
  Echo's Dly < Mod) rests on a handful of percentages, and Reverb's Spin and Chorus Amounts on two to
  four settings; the notes say how many points each law has.
- **Contradictions with the manual** found: Saturator's Waveshaper Curve adds an even-order term,
  Vinyl Distortion's Pinch makes even harmonics, Reverb's Spin depth is a fraction of each tap's delay
  (not milliseconds), Roar's output hard clip comes after Output while its Drive path has a softer
  curve, Vocoder's Depth 0 % is not a constant carrier.

## Settings that did not reach the audio, and values stored off the requested one

- **Auto Pan-Tremolo's Waveform** does not reach the audio: `autopan-shape` and `invert-saw-up` repeat
  the failure of the top 100 (Waveform renders as Sine), so every waveform other than Sine is still
  open (the note's Measured section; INDEX remark).
- **Looper's stored State** does not start recording or playing in a render: the eight cases fit a
  stopped device. The Looper's behaviour needs another way to start it.
- **Chorus-Ensemble's tap count** gave one render for one and two taps at Amount 0; whether it only
  matters with modulation or did not reach the audio is open.
- **Corpus's Tune** at three more values rendered 19 to 28 cents sharp (flagged [measure] in the
  note).
- **Reverb's Smooth**: the first runs read as Size ignored under Fast and Slow; `reverb-smooth-slow`
  did not reproduce that (a Size stored in the set reached the audio under Fast and Slow), so the quirk is
  not general and its cause is open.
- **Four verified cases read back off the requested value**: Glue Compressor `range-15` and `range-40`
  (API values 45.347 and 66.036 for the 45.391 and 66.009 requested; the stored 15 and 40 dB are what the
  note uses), Phaser-Flanger `out+6` (stored +6.0 dB as 1.995; API 0.9988 against 1.0 requested) and
  Shifter `shifter-envelope default` (Env Amount 0 st read back as API 0.5, the other end of the display's
  flat stretch).
- **The export is delay-compensated**, so latency cannot be read from the impulse of a device that
  reports it (Compressor's lookahead, Spectral Resonator, Amp); the notes record the cases where the
  response begins before the impulse.
- **Controls the API does not expose** stay unmeasured: Roar's routing (it loads in Multi Band, so the
  stage-1 shaper and filter runs reached the low band only), Hi-Quality, Resolution and the processing
  order in Spectral Time, the Vocoder's carrier choice and band count, Reverb's Freeze toggled during a
  render. These need the panel or an automation lane.
