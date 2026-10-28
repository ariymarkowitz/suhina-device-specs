# Reverb measurement runs (Live 12.4.6)

Four behaviour runs for [`29.32-reverb.md`](../../live-12/audio-effects/29.32-reverb.md) ›
Measurement plan, made by `make_cases.py` (rerun it after editing; it checks every parameter name
against the dump). The general procedure is `tools/README.md` › 2. This sheet only lists what is
specific to the Reverb.

## Probes

A reverb's tail must die out before the next test signal starts, so these runs use their own
probes instead of `probes/gap2.wav` (gap 2 s). Both are 44.1 kHz. Make them with:

```bash
tools/.venv/bin/python tools/harness/signals.py -o devices/29.32-reverb/probe-gap10/probe.wav --rate 44100 --gap 10
tools/.venv/bin/python tools/harness/signals.py -o devices/29.32-reverb/probe-gap30/probe.wav --rate 44100 --gap 30
```

| Probe | Length | Export length at 120 BPM |
|---|---|---|
| `probe-gap10/` | 118.75 s | 60 bars (1.1.1 to 61.1.1) |
| `probe-gap30/` | 298.75 s | 150 bars (1.1.1 to 151.1.1) |

## Runs

These runs were set up by hand with Build cases. New runs are written as a `runs.py` and built
with `tools/harness/batch.py` (or `make_als.py`), and Live is opened and checked through the
Remote Script (`tools/README.md` › 2b); only the export is done in Live's window.

Each run gets its own Live Set, saved as `<run>` (Live makes `<run> Project/` here; copy that
run's `probe.wav`, `Suhina Probe.amxd` and `suhina_probe.js` into it). Then: drag in `probe.wav`
with Warp off, set the tempo to 120, put Suhina Probe and then Reverb on the track, click
**Build cases** and choose `<run>.json`. Export **All Individual Tracks** as 32-bit WAV, Normalize
off, into `export/` under the export name `<run>`. Save the set as `<run>.als` here.

| Run | Probe | Cases | What it answers (plan step) |
|---|---|---|---|
| `reverb-structure` | gap10 | 20 | predelay versus first reflection (2); reflections alone and tail alone (13); Shape (4); early-reflection taps versus Size (4) |
| `reverb-decay` | gap30 | 12 | T60 versus Decay, 200 ms to 60 s, with the network filters off (5); T60 versus Size at 3.46 s (5); the preset filters' effect (6) |
| `reverb-filters` | gap10 | 20 | Lo Cut and Hi Cut versus Input Freq and Width (3); High filter Shelf versus Lowpass and Low shelf, as decay per band (6) |
| `reverb-texture` | gap10 | 24 | Chorus Amount and Rate (8); Spin Amount and Rate (4); Stereo (11); Density (12); Diffusion and Scale (7), but at Size 100, see below |
| `reverb-size` | gap10 | 22 | Size (4, 5, 7) with Smooth None: reflection times, T60 against Size, tail onset; the tail's onset against Shape (4); Diffusion and Scale at Size 1.53 (7) |

Every run starts with `bypass` (device off), `preset` (the factory preset untouched) and `default`
(the run's base settings: Dry/Wet 100 %, Chorus and Spin off unless the case turns them on).

## Findings that change how to run this

- **Set Smooth to None in any case that sets Size.** With the preset's Smooth = Fast the render ignores a Size set through the API (bit-identical renders for Size 0.22 to 500). `reverb-structure` and `reverb-decay` have such cases (`size-*`, `decay-3.46s-size-*`), and so do the Diffusion and Scale cases of `reverb-texture`; they show nothing about Size. `reverb-size` repeats them with Smooth None (`make_cases.py` `size()`); a Fast case at Size 1.53 is in it as the control.
- **Check the bypass render's impulse before analysing.** `reverb-filters`, `reverb-texture` and `reverb-size` came out 40.00 ms (1764 samples) early, `reverb-structure` and `reverb-decay` exactly aligned. For the three, `analyse.py ... --align -1764` (done in `live/`). Without it the impulse falls outside the analysis window.

Not covered, because they need automation during the render: Freeze, Flat and Cut (plan step 9)
and Smooth (step 10).

## Analysis

```bash
tools/.venv/bin/python tools/harness/analyse.py devices/29.32-reverb/probe-gap10/probe.json \
    "devices/29.32-reverb/export/reverb-structure "*.wav -o devices/29.32-reverb/results
```

(Quote the glob up to the space: `reverb-structure.wav` is the main mix. `probe-gap30/probe.json` for `reverb-decay`; add `--align -1764` for `reverb-filters`, `reverb-texture` and `reverb-size`.) The `.ir.wav` files in `live/` are not in the repository (434 MB, `.gitignore`): rerunning this command on the renders in `export/` makes them again. Points to watch:

- `impulse.rt60_s` comes from a Schroeder curve over the gap only. The curve is cut off at the
  window's end, which makes long decays read short. For Decay of 14.4 s and above, fit the
  energy decay of the `.ir.wav` with the cut-off corrected, or fit only from −5 to −15 dB. It
  also reads far too short whenever early reflections are in the response (0.05 s for a 1.2 s
  tail): the results here are refits of the energy envelope of the `.ir.wav` (both channels
  summed, 20 to 50 ms bins, fit from −5 dB down to −15, −25 or −35 dB).
- Decay per band (`reverb-filters`, the `net-*` cases) is not in `analyse.py`. Filter the
  `.ir.wav` into octave bands and fit each band.
- With long decays the impulse's tail runs into the sweep and the later signals. In `reverb-decay`
  only the impulse results count.
- The sweep response of a time-varying case (Chorus or Spin on) is not valid: read `noise_db`.
