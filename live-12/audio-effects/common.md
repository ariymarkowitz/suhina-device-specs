# Controls and behaviour many devices share

Device notes link here instead of repeating these parts. Where a device departs from what is
written here, its own note says so. Sources are listed at the bottom.

## The title bar

- **Device on/off** (the activator at the left of the title bar): bypasses the whole device.
  Saved in a set as the device's `On` parameter; automatable like any other parameter
  [manual; als 12.4.6].
- **Sidechain header.** Since Live 12.2 the Sidechain toggle sits in its own header at the left
  of the title bar for Auto Filter, Compressor, Corpus, Gate, Glue Compressor, Multiband Dynamics
  and Shifter; the triangle button only unfolds the side-chain settings, and Compressor's
  side-chain filter got its own panel [source: 2].
- **Context menu options** are few and device-specific: Hi-Quality (below), Glue Compressor's
  Oversampling, Delay and Echo's Dry/Wet Equal-Loudness. Compressor, Gate, Limiter and Multiband
  Dynamics have none [manual].
- Hot-swap, preset saving and the rest of the context menu are host features, not part of the
  device.

## Side-chain section

Used by Compressor, Glue Compressor, Gate, Multiband Dynamics, Auto Filter, Corpus, Shifter,
Roar and others; each note says which parts it has [manual 29.9.1].

| Control | Type | Range | Default | Notes | Tag |
|---|---|---|---|---|---|
| Sidechain | toggle | off / on | off | turns the external input on; while off, the device listens to its own input | [manual] |
| Audio From (source) | menu | the set's routing points (tracks, return tracks) | none | which signal drives the detector | [manual] |
| Audio From (tap) | menu | the chosen source's tap points (pre FX, post FX, post mixer) | Post FX [measure] | second chooser under the first | [inferred] |
| Gain (SC Gain) | knob | ±15 dB in Auto Filter's wrapper; other devices [measure] | 0 dB | level of the external signal into the detector only; never heard | [manual]; [source: 1] |
| Dry/Wet (Mix) | knob | 0 – 100 % | 100 % | blend of the device's own input (dry) and the external signal (wet) as the detector's input | [manual] |
| EQ | toggle | off / on | off | filters the detector signal so only a band drives the device | [manual] |
| EQ filter type | buttons | per device [measure] | [measure] | | [measure] |
| Frequency, Q, Gain (EQ) | knobs | per device [measure] | [measure] | Gain only for shelf and peak types | [measure] |
| Listen (headphones) | toggle | off / on | off | replaces the device's output with the detector signal; Gate's display then draws the side-chain level in green | [manual] |

What differs:

- **Not every side-chain has the EQ block.** Multiband Dynamics has none [manual]; Roar's
  side-chain drives only its envelope follower, has no EQ and adds a MIDI note input for its
  feedback tuning [manual].
- The side-chain only drives the detector; the processed signal is always the device's own
  input [manual].
- Compressor's automatic makeup is off while an external side-chain is on [manual 29.9.1].
- Whether the side-chain is band-split in Multiband Dynamics is [measure].
- **Mono Sidechain** is a context-menu option, on by default [source: 5].
- Auto Filter's side-chain drives only its envelope follower. Its EQ offers low shelf, peak,
  high shelf, low-pass, band-pass and high-pass, Q 0.1 – 12, frequency 30 Hz – 15 kHz (wrapper
  bounds) [source: 1]. Treat these as the starting guess for the other devices' side-chain EQ.

## Latency

- Compressor, Gate and Limiter report latency equal to their lookahead; Glue Compressor has no
  lookahead but reports 32 samples (about 0.73 ms at 44.1 kHz) with Oversampling on; Gate is
  reported at a fixed 72 samples. These come second-hand from the help centre's latency article,
  which returned 403 when fetched [source: 3; measure].
- Delay, Echo, Beat Repeat and Filter Delay report none that was found [measure]. Spectral Time
  has a Resolution setting and a Zero Dry Signal Latency option [manual]. Erosion is reported at
  about 2 ms (earlier versions about 5 ms) [source: 3].
- A 2× half-band FIR of 63 taps has 31 frames of latency, one off Glue's 32.
- To measure: render an impulse through the device with the host's delay compensation off and
  read the offset; compare with the latency Live reports in the device's title bar tooltip.

## Hi-Quality and oversampling

Saturator, Pedal, Dynamic Tube, Redux (since 11.2) and Delay offer **Hi-Quality** in the
context menu [manual]. For the distortions it turns on oversampling; the Max wrappers expose it
as an on/off `oversample` and an eco/high `resamplingquality` [source: 1]. In Delay it raises the
interpolation quality of Repitch and Fade [manual]. The oversampling factor is [measure]: render
a high sine (15 kHz) through heavy drive with Hi-Quality off and on and read where the aliasing
products fall. Glue Compressor's separate Oversampling option is 2× [manual].

## Tempo sync of rates and delay times

- Devices with LFOs or delay times choose between a free rate (Hz or ms) and a tempo-synced
  rate. The lists of note values differ between devices; each note gives its own [measure].
- **Sixteenth buttons.** The older delays (Simple, Ping Pong, Filter Delay, probably Grain Delay)
  set the time with buttons 1, 2, 3, 4, 5, 6, 8, 16 (sixteenth notes), one sixteenth being
  `15000 / BPM` ms, plus an Offset of about ±33.3 % that scales the whole delay; free time was
  1 – 300 ms there. Delay and Echo reach 5 s [source: 4].
- **Echo's sync modes:** Notes ×1, Dotted ×1.5, Triplet ×2/3, and 16th as a count of sixteenths
  [manual; source: 1].
- **LFO shapes.** Delay's and Echo's oscillator runs 0.01 – 40 Hz; since 12.4 Delay's LFO has
  Sine, Triangle, Ramp Up, Ramp Down, Square, S&H and Wander with a Morph control, greyed out
  for S&H and Wander [source: 1, 2]. Other devices have their own sets [measure].

## The shared LFO

The modulation devices (Auto Pan-Tremolo, Chorus-Ensemble, Phaser-Flanger, Auto Filter, Shifter
and others) appear to share one LFO design; its Max wrapper (`abl.dsp.stereolfo~`) gives
[source: 1]:

- Waveforms: Sine, Triangle, Analog Triangle, Triangle 8-step, Triangle 16-step, Saw Up, Saw
  Down, Square, Random, Random S&H; the device panels add Wander, Ramp Up/Down and Shark Tooth
  [manual; source: 1]. Each device's note lists which it shows.
- Duty −1 … 1 (warps the shape), stereo Phase 0 – 360°, Spin (right-channel rate is
  `(1 + spin)` × the left) and Offset, which acts as Width for the random shapes [source: 1].
- Rate modes since 12.3 (Auto Pan-Tremolo): Rate (Hz), Time (ms), Synced, Dotted, Triplet, 16th
  [manual]. The note-value lists are [measure].

## Envelope follower

Wrapper `abl.dsp.envfollower~`: attack 0.1 – 30 ms, release 1 – 400 ms [source: 1]. Phaser-Flanger
and Auto Filter use it with a bipolar Amount [manual]; whether every device shares these bounds is
[measure].

## Warmth and Output

Chorus-Ensemble and Phaser-Flanger share a Warmth control (0 – 1 in the wrapper; adds gentle
filtering and saturation) and an Output of −70.6 … +6 dB in the wrapper [source: 1; behaviour
[measure]].

## MIDI side-chain

Shifter, Auto Shift, Corpus, Spectral Resonator and Roar take MIDI from another track to set
pitch [manual]. The chooser picks a track and a tap before or after that track's MIDI effects
[manual]. The audio side-chain above does not apply to them, so a MIDI input route into effects
needs its own design.

## Scales and tuning systems

Since 12.2 Resonators and Spectral Resonator have a **Use Current Scale** toggle and follow the
set's tuning system: pitch controls then count scale degrees or tuning steps instead of
semitones, and Spectral Resonator gains a Quantize option [source: 2]. Auto Shift's quantizer
and Tuner (since 12.1) also read the set's scale or tuning [manual; source: 2].

## Input send and built-in limiters

- Hybrid Reverb's Send and Spectral Resonator's Input Send are dB gains on the processed path
  only; the dry path is untouched. Since 11.1 their arrow-key step is 1 dB, or 0.1 dB with
  Shift [source: 2]. Spectral Resonator's wrapper range is ±24 dB [source: 1].
- Corpus (beside Gain) and Spectral Resonator (beside Input Send) have a built-in limiter with an
  LED that lights when it works [manual]. Threshold and timing are [measure].

## Freeze

Delay, Hybrid Reverb, Reverb and Spectral Time can freeze. Hybrid Reverb's Freeze In keeps
adding new input to the frozen tail; Reverb has Freeze with Flat (no damping while frozen) and
Cut (no new input) [manual].

## Delay-time transitions

Delay offers **Repitch** (the read position glides, so pitch bends like tape), **Fade**
(crossfade between old and new positions) and **Jump** (instant) [manual]. Echo has a Repitch
on/off with a glide time of 0.01 – 1 s in its Max wrapper [source: 1].

## Dry/Wet

- Linear crossfade 0 – 100 % unless a note says otherwise [inferred]; every Max wrapper stores
  it as 0 – 1 [source: 1].
- Delay and Echo have a **Dry/Wet Equal-Loudness** option (context menu; `drywetmode` 0 linear,
  1 equal-loudness in the wrapper) [manual; source: 1].
- Dry/Wet sits at the output in Compressor, Glue Compressor and Drum Buss. In Multiband Dynamics
  and Gate the only Dry/Wet is the side-chain one, which blends detector sources [manual].
- Erosion, Vinyl Distortion and Dynamic Tube have no Dry/Wet in the manual; in Vinyl Distortion
  the global Drive acts as the wet amount [manual].
- To measure: render a sine at 0, 25, 50, 75 and 100 % and fit the law; check whether the dry
  path is delayed to match the wet path's latency.

## Analysers and displays

- EQ Eight's analyser, Spectrum and Tuner pass audio through unchanged [manual]. The
  analysis must run off the audio thread: the callback copies samples into a lock-free queue and
  a UI-side task does the FFT or pitch detection.
- EQ Eight and Spectrum have a button that moves the display between the device chain and the
  main window; Spectrum also toggles it on double-click [manual].
- Tuning systems: Tuner follows the set's tuning system since 12.1; Resonators and Spectral
  Resonator since 12.2 [source: 2].

## Stored values

The `.als` stores the internal value, not the display value. Utility shows the pattern: Gain is
stored as a linear factor, Mid/Side as 0 – 2 (displayed 100M – 100S), Width 0 – 4 (0 – 400 %)
([29.40-utility.md](29.40-utility.md)); Compressor stores Threshold as a linear factor too
([29.09-compressor.md](29.09-compressor.md)). Each note's import mapping must say which scale its
parameters use [measure].

## X-Y displays

Filter Delay, Grain Delay, Delay and EQ-style displays let the user drag a point to set two
parameters at once; in Grain Delay which parameter is on the vertical axis is a view choice, not
a stored parameter [manual].

## Level conventions in the Max wrappers

The wrappers use −70.6 dB as their "minus infinity" floor and often −36 … +36 dB for drive
[source: 1]. These are the wrapper's limits; the panel may show other ranges.

## Sources

1. Cycling '74, Max reference for the Ableton DSP package, `abl.device.*` objects (delay, echo,
   spectraltime, autofilter, compressor, limiter, drumbuss, roar, redux, saturator, utility,
   channeleq) and `abl.dsp.*` building blocks (overdrive, distortion, fuzz, chorus, ensemble,
   vibrato, doubler, flanger, phaser, pitchshifter, ringmod, stereolfo, envfollower,
   pitchestimator): https://docs.cycling74.com/reference/abl.device.delay~ and neighbours; the
   full list is in https://docs.cycling74.com/sitemap.xml. Not found (404): glue, gate, erosion,
   dynamictube, vinyl, amp, cabinet, eq8, eqthree, vocoder. `abl.device.reverb~` is a plate
   reverb, **not** Live's Reverb: do not use its parameters for it.
2. Ableton Live 12 release notes, https://www.ableton.com/release-notes/live-12/ (a long page;
   fetch with offsets around 100 000 and 200 000 to find a device's history).
3. Ableton help centre, latency of Live's devices (via search summaries; the page returned 403),
   https://help.ableton.com/
4. Sound On Sound, "Ableton Live: It's About Time", https://www.soundonsound.com/techniques/ableton-live-its-about-time
5. Auto Filter note, 29.02-auto-filter.md, and its sources
