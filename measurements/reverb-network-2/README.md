# Reverb network identification, second set (Live 12.4.7)

One run, `reverb-network-scale` (`../29.32-reverb/runs.py`), on the base of `../reverb-network/`
(Size 100, Diffusion 0.1 %, Decay 60 s, filters off, reflections at −30 dB, Smooth None): Scale 5,
20, 60, 80 and 100 %, and Size 50 and 200 each with its reflections alone. At Diffusion 0.1 % the
allpasses pass the signal on after their delay, and that delay grows with Scale while the lines'
do not, so each arrival moves with Scale by the allpass length along its path.

State: **built, opened in Live, verified (11 of 11 tracks), exported and analysed**.

- `batch.py build measurements/reverb-network-2/selection.json`: 11 cases on 11 tracks, gap10 probe.
- Export: All Individual Tracks, 44.1 kHz WAV 32-bit, Normalize off, 60 bars, as `reverb-network-2`
  into `export/` (not in the repository).
- `batch.py analyse ... --export measurements/reverb-network-2/export`: offset 0 samples from the
  bypass render; results in `../29.32-reverb/live/reverb-network-scale *`.
