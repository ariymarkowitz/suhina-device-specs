# Live 12 audio effects

One note per device of manual chapter 29. *Note* is `draft` until it has been checked against Live,
`dump checked` once its ranges, defaults, steps, tapers and `.als` names come from the Live 12.4.6
parameter dump (behaviour items can still be `[measure]`).
Shared controls and behaviour (side-chain, LFO, latency, Hi-Quality, dry/wet, MIDI input) are in
[common.md](common.md).

| § | Device | Family | Note | Remarks |
|---|---|---|---|---|
| 29.1 | [Amp](29.01-amp.md) | distortion | dump checked |  |
| 29.2 | [Auto Filter](29.02-auto-filter.md) | EQ, filter, analysis and utility | dump checked | manual and Max wrapper disagree on waves and circuits since 12.2 |
| 29.3 | [Auto Pan-Tremolo](29.03-auto-pan-tremolo.md) | modulation and pitch | dump checked | Live 12.3 replaced the old Auto Pan (kept as Auto Pan Legacy); the note covers the 12.3 device |
| 29.4 | [Auto Shift](29.04-auto-shift.md) | modulation and pitch | dump checked |  |
| 29.5 | [Beat Repeat](29.05-beat-repeat.md) | delay and looping | dump checked |  |
| 29.6 | [Cabinet](29.06-cabinet.md) | distortion | dump checked |  |
| 29.7 | [Channel EQ](29.07-channel-eq.md) | EQ, filter, analysis and utility | dump checked |  |
| 29.8 | [Chorus-Ensemble](29.08-chorus-ensemble.md) | modulation and pitch | dump checked |  |
| 29.9 | [Compressor](29.09-compressor.md) | dynamics | dump checked | first behaviour run done: Threshold, which also showed the Knee is a half-width (tools/README.md › First run) |
| 29.10 | [Corpus](29.10-corpus.md) | reverb and resonance | dump checked |  |
| 29.11 | [Delay](29.11-delay.md) | delay and looping | dump checked |  |
| 29.12 | [Drum Buss](29.12-drum-buss.md) | dynamics | dump checked |  |
| 29.13 | [Dynamic Tube](29.13-dynamic-tube.md) | distortion | dump checked |  |
| 29.14 | [Echo](29.14-echo.md) | delay and looping | dump checked |  |
| 29.15 | [EQ Eight](29.15-eq-eight.md) | EQ, filter, analysis and utility | dump checked |  |
| 29.16 | [EQ Three](29.16-eq-three.md) | EQ, filter, analysis and utility | dump checked |  |
| 29.17 | [Erosion](29.17-erosion.md) | distortion | dump checked |  |
| 29.18 | [External Audio Effect](29.18-external-audio-effect.md) | EQ, filter, analysis and utility | dump checked |  |
| 29.19 | [Filter Delay](29.19-filter-delay.md) | delay and looping | dump checked |  |
| 29.20 | [Gate](29.20-gate.md) | dynamics | dump checked |  |
| 29.21 | [Glue Compressor](29.21-glue-compressor.md) | dynamics | dump checked | stepped lists come from the original third-party design, not Live itself; confirm |
| 29.22 | [Grain Delay](29.22-grain-delay.md) | delay and looping | dump checked |  |
| 29.23 | [Hybrid Reverb](29.23-hybrid-reverb.md) | reverb and resonance | dump checked |  |
| 29.24 | [Limiter](29.24-limiter.md) | dynamics | dump checked |  |
| 29.25 | [Looper](29.25-looper.md) | delay and looping | dump checked |  |
| 29.26 | [Multiband Dynamics](29.26-multiband-dynamics.md) | dynamics | dump checked |  |
| 29.27 | [Overdrive](29.27-overdrive.md) | distortion | dump checked |  |
| 29.28 | [Pedal](29.28-pedal.md) | distortion | dump checked |  |
| 29.29 | [Phaser-Flanger](29.29-phaser-flanger.md) | modulation and pitch | dump checked |  |
| 29.30 | [Redux](29.30-redux.md) | distortion | dump checked |  |
| 29.31 | [Resonators](29.31-resonators.md) | reverb and resonance | dump checked |  |
| 29.32 | [Reverb](29.32-reverb.md) | reverb and resonance | dump checked | `abl.device.reverb~` is a different (plate) reverb; do not use it as a source |
| 29.33 | [Roar](29.33-roar.md) | distortion | dump checked |  |
| 29.34 | [Saturator](29.34-saturator.md) | distortion | dump checked |  |
| 29.35 | [Shifter](29.35-shifter.md) | modulation and pitch | dump checked |  |
| 29.36 | [Spectral Resonator](29.36-spectral-resonator.md) | reverb and resonance | dump checked |  |
| 29.37 | [Spectral Time](29.37-spectral-time.md) | delay and looping | dump checked |  |
| 29.38 | [Spectrum](29.38-spectrum.md) | EQ, filter, analysis and utility | dump checked |  |
| 29.39 | [Tuner](29.39-tuner.md) | EQ, filter, analysis and utility | dump checked |  |
| 29.40 | [Utility](29.40-utility.md) | EQ, filter, analysis and utility | dump checked | best-sourced note (stored values read from our own saved sets) |
| 29.41 | [Vinyl Distortion](29.41-vinyl-distortion.md) | distortion | dump checked |  |
| 29.42 | [Vocoder](29.42-vocoder.md) | modulation and pitch | dump checked |  |
