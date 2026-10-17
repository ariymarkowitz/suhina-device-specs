# Top 100 behaviour runs (Live 12.4.6), in one set

State (2026-10-18, fourth session): **built, opened, verified, exported and analysed, every
run's answer is written into its device note, and the tooling and INDEX are documented** (all
five steps done). Branch `top100-measurements` (not pushed).

## Done in the second session

- `live_check.py open`: 690 tracks in 30 s. `verify`: 802 of 805 cases match
  (`top100.verified.json`). The other 3 are Limiter Ceiling/Threshold at −12 dB: stored as
  −12 dB as asked, but Live's API value is 0.1882 where the harness predicted 0.1719. The display
  has two significant digits, so a run of API values reads "−12 dB" and the harness took the low
  end of it; 0.1882 lies between the dump's −14 dB at 0.125 and −10 dB at 0.25, as −12 dB should.
- **Every clip was Sample Offline** at first (`The file "probe.wav" could not be opened` in Live's
  `Log.txt`): Live 12.4.6 loads no sample of a set that is not in a Project folder, whatever the
  clip's Path says, and the earlier calibration sets had the same problem unnoticed (verify reads
  only devices). `make_als.py` now writes an empty `Ableton Project Info/` beside every set.
- Export: All Individual Tracks, 1.1.1, 60 bars, WAV 32-bit 44.1 kHz, Normalize off, name
  `top100`, into `export/`; 691 files (690 tracks and the Main), 27 GB, 11 GB after `--trim`.
  Live writes a "/" in a track name as "_" in the file name (two tracks); `batch.py` follows that.
- `batch.py analyse --trim`: offset 0 samples from all 36 gap2 and 3 gap10 bypass renders; 690
  renders analysed into the devices' `live/` (`top100.analysis.json`). `summary` runs.
- Silent renders: `utility-gain gain--inf` (expected), `amp-gain gain-0` (Amp gives nothing at
  Input Gain 0) and `beatrepeat-gate gate-1-16` (Gate = Grid: nothing repeats); the last two are
  findings for the notes, not render faults.

## Findings (third session: the device notes)

Every run's answer is written into its device note (`live-12/audio-effects/29.NN-*.md`, a
Measured section, the facts tagged `[measured 12.4.6]`, and a status line under each plan step).
Readings `analyse.py` does not do (high-resolution responses from a 65536-point FFT of the impulse,
spectral peaks of the steady tone, delay tracks against the probe noise, envelopes) were computed
from the renders in `export/`. The headline findings:

**Settings that did not reach the audio.** Some values the set stores, and the Remote Script reads
back, made no difference to the render. Check for bit-identical renders before reading a case:

- Auto Pan-Tremolo: all eight Waveform cases (Triangle to S & H) are bit-identical to Sine.
- Chorus-Ensemble: 1 tap and 2 taps are bit-identical (at Amount 0; may be genuine).
- Beat Repeat: Grid 1/6 and 1/3 replayed 375 and 750 ms slices (dotted 1/8 and 1/4), not 333 and
  667 ms, starting at a 1/16 position that changed from bar to bar. A triplet artefact or a
  generated-set problem; a render with the Grid set by hand would tell.

Bit-identical renders that are genuine (the two states really give the same audio): EQ Three Mid
off and Mid -inf; EQ Eight's high shelf with Adaptive Q on and off; Overdrive Tone 0 and 100 % at
Dry/Wet 0 % (both equal the bypass); Gate Floor 0 dB (the bypass); Phaser-Flanger Doubler 20 ms and
Flanger 20 ms at Amount 0; Vinyl Distortion Tracing with Hard on (Hard/Soft belongs to Pinch); Roar
Blend 0 and 100 % (no Blend in Multi Band) and Morph 0.5 against HP; Spectral Time's default,
Synced 1/8 and 16th Triplet 3 (all 250 ms); Multiband Dynamics Attack 100 ms with Release 0.1 ms
(nothing compressed, so equal to the crossover default).

**Values stored off the requested one.** Some display values were stored at the nearest step the
harness's conversion gives, and the renders show the stored value: Saturator Drive -12, +12 and
+30 dB and Output -12 dB came out as -12.375, +12.375, +30.375 and -12.375 dB (the Color run's
Drive -24 as -23.625); Limiter's Output -12 dB as -12.375 dB. The notes give the stored values.

**Per device:**

- Amp: Gain 0 is silence; each 2.5 of Gain adds 7 to 9 dB of small-signal gain and Volume sets the
  saturated level (-21.5 dBFS at Volume 5 for every Gain). At Gain 5 Bass is perfectly linear, Blues
  nearly so, Lead clips hardest (H3 at the fundamental's level). No model renders noise. Tone
  stack: mid scoop at 570 Hz; Bass and Treble pull the other bands as the manual says.
- Auto Filter: SVF types are one state-variable filter's outputs (high-pass mirrors low-pass
  about Freq; band-pass gain Q at the centre); Res 0 24 dB is two Q 0.5 sections (-12.04 dB at Freq);
  Res 100 % rings at Freq with T60 0.18 s, no self-oscillation. DFM, MS2 and PRD lower their resonance
  as the level rises (6, 12, 14 dB from -60 to 0 dBFS). The envelope moves the cutoff about 7.7
  octaves per unit of peak level at 100 %, linear in amplitude, clamped to the Freq range; Release is
  a one-pole time constant.
- Auto Pan-Tremolo: constant-power law, gain sqrt(2p) (up to +3 dB), L² + R² = 2 at 100 %; Amount
  crossfades linearly with unity; Tremolo uses the same law and keeps the average level.
- Auto Shift: with Pitch Range Mid the 1 kHz sine was taken as 500 Hz; the output is a comb on
  500 Hz x the shift, the spectral envelope kept (formant-preserving at Follow 0). Semitones and
  cents are exact ratios.
- Beat Repeat: in Gate mode the window runs from trigger + Grid to trigger + Gate and replays the
  input from the trigger; Gate = Grid is silent; a new trigger cuts the window; 1 ms fades and
  crossfades.
- Cabinet (Near On-Axis, Condenser): linear at every level, minimum-phase, IRs of 10 to 51 ms, band
  100 Hz to 4 kHz with -28 to -53 dB at 10 kHz; Mono averages L and R.
- Channel EQ: Low cuts keep one shape (half-gain 200 Hz), boosts narrow (101 Hz at +15 dB); Mid is
  constant-Q, 2.51 octaves at every gain; High boosts are a 2.9 kHz shelf, cuts add a low-pass down to
  8.9 kHz at -15 dB.
- Chorus-Ensemble: fixed Delay Time T puts the left tap at T/2 and the right at T/4; the swing is the
  centre x Amount² (so 0 to T at 100 %); Auto and Vibrato sit at 0 ms at Amount 0, Ensemble at 13.6 ms.
- Compressor: slope 1/ratio; RMS reads a sine 3 dB below its peak; the knee is a half-width
  quadratic from 3 to 18 dB; Expand adds (x - T)(1 - 1/r), a slope of 1.5 at ratio 2 (not 2); Attack
  t63 is close to the setting; the Lin release is linear in dB (about 8.7 x (1 - 1/ratio) dB per
  Release time).
- Corpus: Beam is the free-free bar to three decimals, String exact harmonics, Marimba 1 : 3.96 :
  10.67; Pipe and Tube sound 71 and 140 cents flat at Radius 50 %; Tube has odd harmonics only (it
  behaves as closed at one end).
- Delay: Feedback is the displayed percentage as a linear gain per repeat (95 % = -0.45 dB); the
  filter is a 2nd-order Butterworth high-pass and low-pass in series with corners at
  Freq / 2^(Width/2) and Freq x 2^(Width/2), held to 50 Hz to 18 kHz (fits to 0.03 dB), inside the
  loop; no resonance, and the passband loses 1.9 dB at Width 1.
- Drum Buss: not flat even at Drive 0 (Soft): +2 dB of gain, lifts of about 3 dB at 63 to 250 Hz
  and 2 to 8 kHz, 3.9 % THD at -6 dBFS. All three types are odd-symmetric; Medium at Drive 100
  distorts most. Comp: threshold about -20 dBFS, ratio about 3.5:1, makeup +11.1 dB, 90 % attack
  in about 5 ms, release an exponential in dB with 0.40 s; Trim acts before it.
- Dynamic Tube: A and B are clean to -12 dBFS at Bias 0, C has a 2nd harmonic from -60 dBFS; Bias
  50 % costs 6 dB of small-signal gain and adds mainly the 2nd; at Bias 100 % tube A is a dead zone
  up to -12 dBFS. Drive slides the curve along the input axis by its dB value and leaves the
  small-signal gain unchanged. No DC at the output.
- Echo: Triplet x2/3, Dotted x1.5, 16th n x 125 ms, sample-exact; fractional delays use a 4-point
  cubic interpolator. A soft limiter in the loop (also on the first repeat: -0.4 dB at -6 dBFS)
  holds 150 % Feedback at +7.4 dB over the input; Ø inverts every repeat after the first. HP and LP
  are 2nd-order sections at -6 dB at the cutoff (Q 0.5); Res 0.30 is not a plain Q change.
- EQ Eight: every type is the cookbook biquad to 0.003 dB; the 48 dB cuts are four Butterworth
  sections, and Q above 0.71 scales all four section Qs together (1.27 at Q 2, 1.56 at Q 6).
  Adaptive Q multiplies Q by 1.12^(|gain| - 6), the same for cuts, and leaves the shelves alone
  (on and off bit-identical).
- EQ Three: Linkwitz-Riley 4th/8th order, -6.02 dB at each crossover; the mid band is a cascade
  (HP at FreqLo then LP at FreqHi) and the high band also passes the FreqLo high-pass; the flat sum
  dips 0.75 dB (24 dB) and 2.14 dB (48 dB) near the low crossover. Kill = gain 0 (bit-identical to
  -inf).
- Erosion (sine): a pure delay modulation of the whole signal, no dry mix; excursion linear in
  Amount, 0.16 ms peak at 100 % at any Freq. Amount 0 is a 0.2-sample fractional delay, not a
  bypass. The base delay is hidden by Live's delay compensation.
- Filter Delay: times exact to 0.003 ms; Swing scales the whole synced delay by (1 + swing); the
  filter is Delay's (same corners and clamps). The feedback inverts the polarity of each repeat
  and adds one sample per pass; the filter is in the loop.
- Gate: opens at the first 3 dB step above Threshold; open is exactly unity, closed exactly Floor
  at every level (Floor 0 renders like the bypass). Attack and Release are one-pole time constants
  of the linear gain (63 % at the knob value); the release starts 28 ms after the level drops.
- Glue Compressor: the knee widens as the ratio falls (Ratio 2 already takes 1.3 dB 10 dB under
  Threshold) and the slope never settles at the ratio. Attack is near a 63 % time from 10 ms up;
  Release is an exponential in dB with tau 0.8 x the knob at 0.1 s and 0.34 x at 1.2 s. Auto: a
  fast 1.5 dB part (42 ms) and a slow one (about 5 s) that still held 6.5 dB from the staircase
  2 s earlier.
- Grain Delay: at Pitch 0 the grain rate has no effect (a plain delay with a linear interpolator);
  shifted pitch lands on lines 1 kHz + n x grain rate, so +0.5 st does nothing at 60 Hz and the
  error is up to half the grain rate; L and R carry antiphase amplitude modulation.
- Hybrid Reverb (Dark Hall): the Decay display is near the T60 of the 125 Hz to 1 kHz bands from
  1 s up (3.5 s gives a full-band T30 of 3.25 s, 1.7 s at 8 kHz); 0.1 s is not reached (0.25 s in
  every band). Shimmer at 3.5 s decays in 5.9 s. Dark Hall starts at 4.5 ms with no discrete early
  reflections; Quartz has sparse reflections, Prism about 300 equal pulses per second. The
  harness's `rt60_s` and `noise_db` (186 ms window) do not suit reverbs.
- Limiter: a hard ceiling to 0.01 dB with no knee, overshoot or undershoot; Gain is a pre-gain;
  Maximize adds -Threshold, limits at 0 dBFS, then applies Output. Lookahead is the whole attack;
  Release is a one-pole time constant of the linear gain; Auto recovered with 220 ms after a 1 s
  burst. The "Output -12 dB" case was stored as -12.375 dB.
- Multiband Dynamics: 4th-order Linkwitz-Riley crossovers (-6.02 dB at each), the bands sum flat
  to 0.01 dB but as an all-pass (4 ms of group delay at 120 Hz); no lookahead. Above slopes fall
  short of (1 - 1/R) (0.46, 0.64, 0.77 dB/dB at 1:2, 1:4, 1:Inf); the detector is after Input gain;
  RMS and Peak give the same gain. Attack and Release are not 63 % times (63 % at about 0.11 x the
  knob); Time scales both. `time att-100ms` equals the crossover default because with Release
  0.1 ms nothing is reduced, not because the setting failed.
- Overdrive: Drive adds 9 dB of small-signal gain per 25 %; Drive 0 still adds 13.6 % THD from
  -24 dBFS. Dynamics 100 % starts the distortion 18 dB lower in level but keeps the output rising
  (+7.7 dBFS at full scale); Dynamics 0 % is a soft clipper at -0.3 dBFS. Tone tilts from low-pass
  to high-pass about 250 Hz; at Dry/Wet 0 % Tone does nothing (bit-identical to bypass),
  contradicting SOS.
- Pedal: Overdrive is a soft odd-only curve (saturates at -5.1 dBFS), Distortion a hard clipper at
  about -14.5 dBFS, Fuzz asymmetric with the 2nd harmonic strongest (72 % THD). Gain 0 % is not
  0 dB (+6 to +13 dB); the Gain taper differs per circuit.
- Phaser-Flanger: N notches from N identical second-order all-passes at Center, output 0.5 dry +
  0.5 chain; Spread sets the section Q (2.0, 0.50, 0.10 at 0, 50, 100 %). Flanger and Doubler taps
  arrive at Time + 1 sample, both at 0.5, so Dry/Wet 100 % still holds the dry. The LFO works in
  octaves: Flanger Time x 2^(-3A(1 - sine)) (6 octaves at 100 %), Doubler Time x 2^(A/2 sine),
  Phaser +-4 octaves of Center. Feedback H = 0.5 (1 + W)/(1 - g W), no limiter at 99 %; Ø inverts
  the whole wet branch. Doubler 20 ms and Flanger 20 ms are genuinely the same plain delay at
  Amount 0.
- Redux: Rate is the true sample rate (aliases at m x Rate +- f) through a zero-order hold (sinc
  images to 0.1 dB); the quantiser is mid-tread with step 2^(1 - Bits), and 1 and 2 bits are also
  scaled (0.5, 0.707), so 1 bit gives {0, -0.5}; a one-pole DC blocker at about 5 Hz follows. The
  Post filter's corner is Rate/2 x 2^octave, about 96 dB/oct. Impulse readings depend on the hold
  clock and are not usable.
- Resonators: Note n sounds at 440 x 2^((n - 69)/12) Hz but flat by one sample of loop length
  (5 cents at C2, 42 at C5); no direct sound, the first echo one period late. Decay 0 to 100 gives
  T30 up to 2.8 s at C2 (about 0.00066 x Decay^1.81 s). Mode B is Mode A with alternate echoes
  inverted (an octave lower). Const is not constant at the range ends.
- Roar: the device loads in Multi Band (stored 3), crossovers at 200 Hz and 2 kHz with
  Linkwitz-Riley-like 24 dB/oct skirts and a flat sum; an off stage is silent and Blend does
  nothing there. So the shaper and filter runs only reached the low band: the 1 kHz curves are not
  answered. The output stage is a soft clip near 0 dBFS, not a hard clip. Morph 0.5 renders
  bit-identically to HP.
- Saturator: Soft Sine is sin(pi/2 u) clamped at 1, Sinoid Fold the same sine unclamped; Medium
  Curve has slope 2 and is flat at 1.000 from about 0.65 (not tanh-like); Analog Clip is linear
  to 0.708; Hard Curve has slope 6.8 and no linear region; Bass Shaper (-50 dB) follows 1 - exp(-u);
  all odd-symmetric. Drive and Output are exact gains; Dry/Wet 50 % is 0.5 dry + 0.5 wet. Color at
  +100 %: Amt Lo a +36 dB low shelf, Amt Hi a +23 dB bell; with a linear curve the inverse filter
  cancels them exactly. Drive -12/+12/+30 and Output -12 were stored as -12.375, +12.375, +30.375
  and -12.375 dB.
- Shifter: Pitch mode is exact to 0.3 cent with +2.54 dB of gain and sidebands at
  2 |ratio - 1| / Window; latency at 0 st is half the Window (40 ms). Freq mode is a single
  sideband (image -70 dB); shifting through 0 Hz leaves only -53 dB. Delay: set time + 1 sample,
  Tone a one-pole low-pass in the loop, Dry/Wet equal-power.
- Spectral Resonator: partial n at Freq x (1 + (n - 1)(1 + Stretch/100)) to 0.07 Hz; nothing above
  about 20 kHz; Decay is a true T60 (within 0.5 %); noise input gives steady sinusoids far
  narrower than a linear resonator of that decay. The response starts 546 samples before the
  impulse in the export (delay compensation).
- Spectral Time: delay times are rounded to whole 256-sample steps (up to 2.9 ms off at 44.1 kHz,
  Mid resolution), with no added latency and clean single-sample echoes.
- Utility: Width is a plain side gain (L = M + w S), no normalisation; Gain is exact (-inf is
  digital silence, +35 dB unclipped); Bass Mono leaves the mid alone and puts a 3rd-order
  Butterworth high-pass on the side (-3 dB at the set frequency), not a Linkwitz-Riley crossover.
- Vinyl Distortion: Hard/Soft acts only on Pinch (tracing default and hard bit-identical). Pinch
  makes even harmonics only (contrary to the manual's odd), opposite in L and R, with a DC offset
  of +-0.32 at -12 dBFS and no DC blocker; Soft adds about 4 x Drive x |x|, Hard a pure square
  term. Tracing is H2-led with some H3. Both models compute their distortion from L + R.
- Vocoder (internal noise carrier, 20 bands as loaded, geometric from 80 Hz to 12 kHz): BW is the
  width relative to the band spacing (100 % tiles flat); Retro keeps the centres but tilts the
  gains. Depth 0 % is not a constant carrier (output follows the input at 0.24 dB/dB), contrary to
  the manual; Depth 150 and 200 % expand to silence below -48 and -36 dBFS. Gate passes a tone about
  10 dB under the displayed threshold. Attack and Release are one-pole, tau about 0.27 and 0.22 x
  the knob. Noise X is a sample-and-hold at the Rate; Crackle 0 % still gives about 80 impulses per
  second.

## What is here

- `selection.json`: the 100 runs, the set name (`top100`) and the two probes. Every run is a
  priority-1 candidate (see below) except 25 left out to make 100.
- `top100.als`: one Live Set, **690 tracks for 805 cases**. Each run's `bypass`, and any case
  that two runs share, plays on one track (`make_als.py build --share`). Tracks are ordered by
  probe: the gap2 tracks first, then the gap10 tracks (32 tracks: Hybrid Reverb algorithms and decay,
  Resonators decay, Spectral Resonator decay). Every clip points at one of the two shared probe
  files (`../probe.wav`, `../29.32-reverb/probe-gap10/probe.wav`); nothing is copied.
- `top100.cases.json`: per case, its track, probe, and each parameter's API and stored value.
- Each run's cases file is written beside its device's `runs.py` (`measurements/29.NN-*/<run>.json`).

The candidates: three Sonnet agents read every note's Measurement plan and wrote
`measurements/29.NN-*/runs.py` for all 42 devices: 257 runs, priority 1 (125), 2 (100) and 3 (32),
each with `question`, `plan` step, `read` (which analysis answers it) and `why`. `batch.py check`
passes on all of them. Spectrum, Tuner, Looper and External Audio Effect only have token
priority-3 runs; little about them can be measured from audio with static settings.

## Tooling added in this session

- `tools/harness/batch.py`: `check`, `build`, `analyse`, `summary`; see its docstring.
- `make_als.py build`: `--share` (one track per identical device state and probe) and a
  per-cases-file `"probe"`.
- `live_check.py open <set>`: opens a set (`open -a`) and waits through the Remote Script until it
  is loaded; `verify` follows each case's `track`.
- Tests: `tools/harness/tests/test_batch.py` and new tests in `test_make_als.py`; all 57 pass.
- `AGENTS.md` (repository root): drive Live through the AbletonMCP Remote Script, not its window.
- `tools/README.md` › 2b, `measurements/29.32-reverb/README.md`, `README.md`: pointers to that.
- A trial (`compressor-ratio` alone) was built, opened with `live_check.py open` and passed
  `verify` with 0 problems in Live 12.4.6.

## Next steps

`PY=tools/.venv/bin/python`

1. Done. **Open and verify** (Remote Script, no UI):
   ```bash
   $PY tools/harness/live_check.py open measurements/top100/top100.als --timeout 900
   $PY tools/harness/live_check.py verify measurements/top100/top100.cases.json -o measurements/top100/top100.verified.json
   ```
   690 tracks is far more than any earlier set (37 to 91); if Live struggles, split the selection
   into two selection files and build two sets.
2. Done (all tracks at once). **Export: the one UI step.** Ask the user first whether they will click it or allow control of
   Live (the user declined desktop control once in this session and asked for the MCP route).
   File › Export Audio/Video, WAV, 32-bit, 44.1 kHz, Normalize off, into `measurements/top100/export/`.
   Either: all tracks at once, name `top100`, length 60 bars (the gap10 probe, 118.75 s), then
   `analyse --trim`; that needs about 690 × 42 MB ≈ 29 GB until the trim. Or two exports (less disk):
   select the gap2 tracks, Selected Tracks Only, 24 bars, name `top100`; then the gap10 tracks
   (the last 32), 60 bars, name `top100-gap10`.
3. Done. **Analyse and summarise:**
   ```bash
   $PY tools/harness/batch.py analyse measurements/top100/selection.json --export measurements/top100/export [--trim]
   $PY tools/harness/batch.py summary measurements/top100/selection.json > <scratch>/summary.txt
   ```
   `analyse` takes each probe group's offset from its bypass renders (an export has come out 40 ms
   early before) and writes into each device's `live/`.
4. Done. **Update the device notes** (`live-12/audio-effects/29.NN-*.md`): every run's answered
   plan step has a `[measured 12.4.6]` fact and a status line (Findings above). The readings
   `analyse.py` does not do were computed from the renders; `analyse.py`'s `rt60_s` and `noise_db`
   do not suit reverbs, and its attack/release and FM figures failed for several devices (the notes
   say where).
5. Done. **Document**: the findings above; `tools/README.md` › 2b (`--share`, the Project folder,
   export names, a `batch.py` section) and › Limits (display values stored at a rounded sample;
   `analyse.py`'s reverb and envelope figures); the INDEX's status (`partly measured`) and remarks
   for the re-runs and surprises; `.gitignore` already leaves out the `.ir.wav` files and Live's
   `Samples/`.

## Known points from the candidates

- Roar's routing mode is not an API parameter: every Roar run plays in the loaded mode.
  `roar-routing-default` showed it is Multi Band, so stage 1 sees only the band below 200 Hz and
  the shaper and filter runs at 1 kHz did not reach their stage. They need the Single routing,
  set on the panel.
- Corpus has two parameters named Width: `Width` is the filter bandwidth, `Width #2` the stereo width.
- Glue Compressor's Ratio, Attack and Release are set by index (no item names in the API).
- Beat Repeat runs use the impulse at bar 1 as the trigger reference.
- Not measurable this way: automation, side-chain, MIDI, Hi-Quality/Oversampling, the Hybrid
  Reverb IR choice, Vocoder carrier and band count, Spectral Time resolution, Utility Mid/Side.
