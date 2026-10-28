# Reverb network identification (Live 12.4.7)

One run, `reverb-network-id` (`../29.32-reverb/runs.py`): the Reverb's bare tail network at Size 100,
Diffusion 0.1 %, Decay 60 s, network filters off and the reflections at their minimum (−30 dB),
with Smooth None. Its cases vary Shape, Stereo, Density, Diffusion (60 %) and Scale (5 %), and
`er-only` holds the reflections alone at the same level (its tail is the same network at −30 dB,
so the bare tail is `(default − er-only) / (1 − 0.03)`).

State: **built, opened in Live, verified (13 of 13 tracks), exported and analysed**.

- `batch.py build measurements/reverb-network/selection.json`: 13 cases on 13 tracks, gap10 probe.
- Export: All Individual Tracks, 44.1 kHz WAV 32-bit, Normalize off, 60 bars, as `reverb-network`
  into `export/` (not in the repository).
- `batch.py analyse ... --export measurements/reverb-network/export`: offset 0 samples from the
  bypass render; results in `../29.32-reverb/live/reverb-network-id *`.
