# Side-by-side comparison with Live

Plays the same sample through a Live device and the
Suhina device with the same settings, and lets you switch between them by ear.

```
samples/          WAV loops to listen with (made by make_samples.py; not in git)
build_set.py      sample + device's cases -> a Live Set in sets/<device>-<sample>/
render_suhina.py  the same set through suhina-cli -> sets/<name>/suhina/
index.html        the comparison page (no build step)
sets/<name>/      set.als, export/ (Live's renders), suhina/ (Suhina's renders) (not in git)
```

Run from the repository root; `PY` is `tools/.venv/bin/python`.

## 1. Samples (once)

```bash
tools/.venv/bin/python compare/make_samples.py
```

Two synthetic 10 s samples, 44.1 kHz stereo: `impulse` (one sample at 0.5 s, then silence for the
tail) and `white-noise` (5 s of noise, independent on each side, then 5 s of silence). Any other 44.1 kHz WAV works too: pass its path.

## 2. Build the set

```bash
tools/.venv/bin/python compare/build_set.py compressor white-noise [--run compressor-threshold]
```

Takes the device's cases (`devices/<device>/cases/`, every run unless `--run`) with the sample in
place of each probe; runs that need a side-chain key or MIDI are skipped. Writes
`compare/sets/compressor-white-noise/set.als` and prints the commands below.

## 3. Export from Live

```bash
tools/.venv/bin/python tools/harness/live_check.py open compare/sets/compressor-white-noise/set.als
```

Then **File › Export Audio/Video** (the one UI step; Live's API cannot export):

| Setting | Value |
|---|---|
| Rendered Track | All Individual Tracks |
| Start / Length | 1.1.1, **5 bars** (10 s at 120 BPM) |
| File type | WAV, 32-bit, 44100 Hz |
| Normalize / Dither / Create Analysis File | off |
| Folder | `compare/sets/compressor-white-noise/export/` |
| Export name | `compressor-white-noise` (what `build_set.py` prints) |

Live writes `compressor-white-noise <run> <case>.wav`; the page expects exactly that. Ignore the
`compressor-white-noise.wav` main mix.

## 4. Render through Suhina

```bash
tools/.venv/bin/python compare/render_suhina.py compressor-white-noise
```

Uses `../suhina-daw/target/release/suhina-cli` (build it with `cargo build --release -p
suhina-cli` there, or give `--cli`). A device Suhina does not have yet must fail or be silent,
never pass audio through unnoticed: look at the page's stats row for B.

## 5. Compare

```bash
python3 -m http.server -d compare 8000
```

Open <http://localhost:8000/>. (A server is needed because the page reads the folders' listings
and decodes the WAVs with `fetch`.)

- Pick a set, then a case. The list shows cases missing a render.
- **A** is Live, **B** is Suhina, **A − B** the difference; playback stays in sync and switches at
  the same position. Keys: `1` `2` `3`, `Tab` A/B, `Space` play, up/down next case.
- "match B's level to A" removes an overall level gap so you hear tone, not loudness.
- Stats show peak and RMS of each and the difference below A. For numbers against Live's
  tolerances use `tools/harness/compare.py` (`tools/README.md` › 3); the page is for listening.
