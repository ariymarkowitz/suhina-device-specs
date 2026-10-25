# Fourth set: the eight candidate runs left open by the third set (Live 12.4.7)

The eight runs added to the devices' `runs.py` after the third set, each to answer what a third-set
render could not. `selection.json` lists them; `fourth.als` is the set.

State: **built, opened in Live, verified, exported, analysed, and the answers written into the
device notes** (each note's Measured › Fourth set, or Third set for the Compressor, Delay and
Phaser-Flanger, whose notes keep the run beside the third-set run it repeats).

| Run | Device | Cases | Probe | Answer (note) |
|---|---|---|---|---|
| `compressor-peak-buzz-eq-off` | Compressor | 5 | extended | [Behaviour](../../live-12/audio-effects/29.09-compressor.md#behaviour) |
| `delay-time-jump-noise` | Delay | 5 | 2 s | [Measured](../../live-12/audio-effects/29.11-delay.md#measured) |
| `phaser-flanger-env-times-small` | Phaser-Flanger | 6 | extended | [Measured](../../live-12/audio-effects/29.29-phaser-flanger.md#measured) |
| `spectral-resonator-mod-rate` | Spectral Resonator | 7 | 2 s | [Measured › Fourth set](../../live-12/audio-effects/29.36-spectral-resonator.md#fourth-set-live-1247) |
| `spectral-resonator-dialmode-conflict` | Spectral Resonator | 4 | 10 s | the same |
| `spectral-time-order-reference` | Spectral Time | 4 | 2 s | [Measured › Fourth set](../../live-12/audio-effects/29.37-spectral-time.md#fourth-set-live-1247) |
| `vocoder-band-counts-bw25` | Vocoder | 10 | 2 s | [Measured › Fourth set](../../live-12/audio-effects/29.42-vocoder.md#fourth-set-live-1247) |
| `vocoder-pitch-limits` | Vocoder | 4 | extended | the same |

- `batch.py build measurements/fourth/selection.json`: 8 runs, 45 cases on 40 tracks (each run's `bypass` and `default` are among its cases; the bypass of a device and any case another
  run already has play on one track). `live_check.py verify`: all 45 cases match, 0 problems
  (`fourth.verified.json`).
- Export: every track at once under the name `fourth`, 60 bars (the 10 s probe's length), 44.1 kHz WAV
  32-bit, Normalize off, into `export/` (not in the repository, 930 MB for 41 files).
- `batch.py analyse --trim` into the devices' `live/` (`fourth.analysis.json`: the export's offset
  against each probe is 0 samples in all three groups).
- The figures in the notes come from the raw renders with one-off scripts (not kept in the repository), not from `analyse.py`'s
  fields (the runs ask about waveforms over time, spectra of the noise and comb lines); the
  definitions are in the notes' paragraphs.

## What the runs showed

- **Compressor**: with the side-chain EQ off, Peak at the fastest Attack and Release follows the 50 Hz
  waveform (21.7 % THD, odd harmonics, the 3rd at -14.2 dB); Release 100 ms or RMS brings it to 1.5 %.
  The 3.1 % of the third set was the loaded preset's 80 Hz detector high-pass.
- **Delay**: a lane's step of L Time from 100 to 200 ms is sample-exact and identical in Repitch, Fade
  and Jump even on noise (no glide, no crossfade): the smoothing modes are not tested by a stepped
  lane. A ramped lane is the open candidate (`delay-time-ramp-noise`).
- **Phaser-Flanger**: with the delay in its linear range (Time 20 ms, Env Amount +0.1) the follower's
  Release is a pole of about the setting (90 % back in 2.25 times Release) and Attack 30 ms takes 24 ms
  to half; the delay under a -6 dBFS burst is 31 % shorter than under the -30 dBFS bed.
- **Spectral Resonator**: Mod Rate speeds the wandering up in Chorus and Wander; the stored frequency
  dial mode 0 is the Hertz dial and 1 the note dial.
- **Spectral Time**: stored `ProcessingOrder` 0 is Frz > Dly (the hold is heard 250 ms after the
  freezer's tick), 1 is Dly > Frz (the freezer captures the delayed input; a sound between two ticks can
  be lost).
- **Vocoder**: the stored BandCount 0 to 7 gives 4, 8, 12, 16, 20, 24, 28 and 32 bands. The Pitch
  Tracking limits decide what is tracked (a 50 Hz tone at Low 30 Hz) but outside them the oscillator
  parks at a value that is not a limit (215.7, 415.4 Hz or the last pitch).

## Left open

The rule for the Vocoder's parked pitch, Mod Rate's unit in Hz and in Granular, the Delay's ramped time
(`delay-time-ramp-noise`) and the other points listed in
[`../third/README.md`](../third/README.md) › Settings that did not read, and what is open, were all taken
up in the fifth set ([`../fifth/README.md`](../fifth/README.md)): the Vocoder's oscillator keeps its last
tracked pitch at the loaded limits, Mod Rate is Rate / 3 Hz in Chorus, and the Delay's ramp is read.
