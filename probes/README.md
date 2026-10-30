# Probe signals

The test signals the runs play through a device (stereo, 44.1 kHz, 32-bit float WAV), each with a
manifest (`<name>.json`) saying where every signal starts. A run names its probe with `"probe"` in
its `runs.py` (default `gap2`; its cases file in `devices/<device>/cases/` repeats it).

| Probe | Length | Used for |
|---|---|---|
| `gap2` | 47 s | the main probe: impulse, sweep, level staircase, bursts, steady tone, noise, left/right, silence, with 2 s of silence after each |
| `gap10` | 119 s | the same with 10 s gaps, for reverbs and long delays |
| `ext` | 86 s | the extended probe: more staircases, short bursts, aliasing tones, ramps, a glide, an impulse train (`signals.py --kind ext`) |
| `fifth` | 42 s | fs/4 tones, 20 Hz and 5 kHz staircases, a sequence of tones (`--kind fifth`) |
| `key-duck`, `key-saw`, `key-noise` | 47 s | side-chain keys, timed against `gap2` |
| `gap30` | 299 s | the same with 30 s gaps. Over GitHub's file limit and used by no run, so only its manifest is kept; `python tools/harness/probes.py gap30` makes it |

**To compare a Suhina device with Live:** play the run's probe through the device with each case's
settings from `devices/<device>/cases/<run>.json`, save one WAV per case, and analyse and compare
as in `tools/README.md` › 3. Live's renders were delay-compensated, so a render lines up with its
probe. **To measure Live:** `measure.py build` points the set's clips at these files.

They are made by `tools/harness/signals.py` (`probes.py` has the arguments; the noise is seeded)
and are identical when made again. Do not edit them: results are tied to these exact samples.
