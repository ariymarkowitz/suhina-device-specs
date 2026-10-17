# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Vocoder behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.42-vocoder.md › Measurement plan.

The modulator is the probe, the carrier the device's own noise (the loaded Carrier: Noise). Where a run
asks about the carrier or the bank alone it sets Depth 0 %, which the manual says discards the
envelope, so the output is the carrier through the synthesis bank at constant gain whatever the
modulator does. Band layouts are read from a long FFT of the noise segment of the render (the
1/6-octave `noise_db` is too coarse for 4 to 40 bands).

Left out (cannot be measured this way): the Carrier choice (External, Modulator, Pitch Tracking) and
everything that depends on it, i.e. plan 8 (pitch tracking: High/Low, waveform, Pitch), 9's
external-carrier part, 10's spoken sentence and 4's synth carrier, because the chooser is not an API
parameter and there is no second track; Bands (not an API parameter: the loaded count is used, which
the first run shows); latency and CPU per Bands (plan 14); the band display's per-band levels.
"""

DEVICE = "Vocoder"

ON, OFF = 1, 0
# The carrier through the bank at constant gain: Depth 0, no unvoiced noise, wet only.
CARRIER = {"Envelope Depth": {"display": 0}, "Dry/Wet": {"display": 100}, "Enhance": OFF,
           "Unvoiced Level": {"norm": 0.0}}
# The classic setting: Depth 100 %.
CLASSIC = {**CARRIER, "Envelope Depth": {"display": 100}}

RUNS = [
    {"name": "vocoder-bank", "plan": "2, 3", "probe": "gap2", "read": ["noise (long FFT of the render's noise segment)"], "priority": 1,
     "why": "the band layout (count of the loaded setting, centre spacing, -3 dB widths) against BW, Precise/Retro and Range",
     "question": "band centres, widths and gains in the output spectrum at Depth 0 %: BW 25 % and 200 %, Retro, Range 500 Hz to 4 kHz, Range 20 Hz to 18 kHz (default: BW 100 %, 80 Hz to 12 kHz, Precise)",
     "base": CARRIER,
     "cases": [["bw-25", {"Filter Width": {"display": 25}}], ["bw-200", {"Filter Width": {"display": 200}}],
               ["retro", {"Precise/Retro": ON}],
               ["range-500-4k", {"Lower Filter Band": {"display": 500}, "Upper Filter Band": {"display": 4000}}],
               ["range-20-18k", {"Lower Filter Band": {"display": 20}, "Upper Filter Band": {"display": 18000}}]]},

    {"name": "vocoder-noise-carrier", "plan": "7", "probe": "gap2", "read": ["noise (long FFT)", "raw render (density)"], "priority": 1,
     "why": "the Noise carrier's X axis (sample-rate reduction: alias images, band limit) and Y axis (density: sparse impulses to full noise)",
     "question": "spectrum and time-domain look of the carrier at Depth 0 % for Noise Rate 100 Hz, 1.41 kHz, 5.32 kHz and Crackle 50, 10, 0 % (default 20 kHz, 100 %)",
     "base": CARRIER,
     "cases": [["rate-100", {"Noise Rate": {"display": 100}}], ["rate-1410", {"Noise Rate": {"display": 1410}}],
               ["rate-5320", {"Noise Rate": {"display": 5320}}],
               ["crackle-50", {"Noise Crackle": {"display": 50}}], ["crackle-10", {"Noise Crackle": {"display": 10}}],
               ["crackle-0", {"Noise Crackle": {"display": 0}}],
               ["rate-100-crackle-10", {"Noise Rate": {"display": 100}, "Noise Crackle": {"display": 10}}]]},

    {"name": "vocoder-envelope", "plan": "4", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "the envelope followers' Attack and Release times against the knobs (what 63 % and 90 % mean for a band)",
     "question": "rise at the -30 to -6 dBFS burst edge and fall at -6 to -30 for Attack 5.6, 31.6, 178 ms and Release 74, 548 ms, 4.05 s (Depth 100 %; default 1 ms and 150 ms)",
     "base": CLASSIC,
     "cases": [["att-5.6ms", {"Attack Time": {"display": 0.0056}}], ["att-31.6ms", {"Attack Time": {"display": 0.0316}}],
               ["att-178ms", {"Attack Time": {"display": 0.178}}],
               ["rel-74ms", {"Release Time": {"display": 0.074}}], ["rel-548ms", {"Release Time": {"display": 0.548}}],
               ["rel-4s", {"Release Time": {"display": 4.05}}]]},

    {"name": "vocoder-depth-gate", "plan": "5, 6", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the Depth curve (output level against input level at 0 to 200 %) and the Gate's threshold and knee",
     "question": "staircase output level for Depth 0, 50, 150, 200 % and Gate -30 and -10 dB at Depth 100 %",
     "base": CLASSIC,
     "cases": [[f"depth-{d}", {"Envelope Depth": {"display": d}}] for d in (0, 50, 150, 200)]
     + [["gate--30", {"Gate Threshold": {"display": -30}}], ["gate--10", {"Gate Threshold": {"display": -10}}]]},

    {"name": "vocoder-formant", "plan": "12", "probe": "gap2", "read": ["steady (spectrum)"], "priority": 2,
     "why": "the Formant unit (semitones?) and what happens at the Range edges: where the 1 kHz modulator's energy lands in the carrier",
     "question": "centre of the output band for the 1 kHz tone with Formant -12, -5, +5, +12, +24 (BW 50 %, Depth 100 %)",
     "base": {**CLASSIC, "Filter Width": {"display": 50}},
     "cases": [[f"formant{f:+d}", {"Formant Shift": f}] for f in (-12, -5, 5, 12, 24)]},

    {"name": "vocoder-unvoiced", "plan": "10", "probe": "gap2", "read": ["silence", "noise (long FFT)", "dynamics"], "priority": 2,
     "why": "the Unvoiced noise: level against the knob, whether it is high-passed, Sens. as always-on/off, Fast against Slow",
     "question": "level and spectrum of the unvoiced noise in silence (Sens. 100 %) at 0, -10, -20 dB; Sens. 0 % and 50 % Fast and Slow at 0 dB with the noise segment as modulator",
     "base": {**CLASSIC, "Unvoiced Level": {"display": 0}, "Unvoiced Sensitivity": {"display": 100}},
     "cases": [["unv--10dB", {"Unvoiced Level": {"display": -10}}], ["unv--20dB", {"Unvoiced Level": {"display": -20}}],
               ["sens-0", {"Unvoiced Sensitivity": {"display": 0}}],
               ["sens-50-fast", {"Unvoiced Sensitivity": {"display": 50}}],
               ["sens-50-slow", {"Unvoiced Sensitivity": {"display": 50}, "Unvoiced Speed": {"item": "Slow"}}]]},

    {"name": "vocoder-output-modes", "plan": "11, 9, 13", "probe": "gap2", "read": ["stereo", "static"], "priority": 3,
     "why": "Mono/Stereo/L-R channel handling, Level's range, Dry/Wet law and what Enhance does to the carrier",
     "question": "2x2 matrix (left-only and right-only 1 kHz) for Mono and L/R (default Stereo); staircase for Level +12 and -12 dB, Dry/Wet 50 %, Enhance on",
     "base": CLASSIC,
     "cases": [["mono", {"Mono/Stereo": {"item": "Mono"}}], ["lr", {"Mono/Stereo": {"item": "L/R"}}],
               ["level+12", {"Output": {"display": 12}}], ["level-12", {"Output": {"display": -12}}],
               ["dw-50", {"Dry/Wet": {"display": 50}}], ["enhance", {"Enhance": ON}]]},
]
