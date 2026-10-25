# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Vinyl Distortion behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.41-vinyl-distortion.md › Measurement plan.

Harmonics are read from the staircase (1 kHz sine, -60 to 0 dBFS in 3 dB steps: output level, THD
and harmonic levels per input level), so the distortion amount against level and Drive is a table.
The probe's tone is identical in L and R, which is what the Pinch stereo question needs: the
odd harmonics in L and R are compared in the raw renders (their relative sign), which analyse.py
does not do; `read` says so. The Crackle runs rely on the renders being 46.75 s long: clicks
are counted over the quiet gaps and under the signals.

Left out (cannot be measured this way): steady tones other than 1 kHz, so the band-pass shape is
read only through the Freq and Width cases against the one tone (and the sweep's harmonics); the XY
pad's Alt-drag (a UI action); whether the crackle repeats between two renders (a case renders once;
compare the quiet gaps within a render instead).
"""

DEVICE = "Vinyl Distortion"

ON, OFF = 1, 0
# One model at a time, band centred on the 1 kHz test tone, Soft, Stereo, no crackle, Global Drive full.
TRACING = {"Tracing On": ON, "Pinch On": OFF, "Tracing Drive": {"display": 0.5}, "Tracing Freq.": {"display": 1000},
           "Global Drive": {"display": 1}, "Crackle Volume": {"display": 0}}
PINCH = {"Tracing On": OFF, "Pinch On": ON, "Pinch Drive": {"display": 0.5}, "Pinch Freq.": {"display": 1000},
         "Global Drive": {"display": 1}, "Crackle Volume": {"display": 0}}

RUNS = [
    {"name": "vinyl-distortion-tracing", "plan": "2, 4, 6", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "Tracing's even-harmonic distortion against Drive, level, band Freq and Width, and Soft against Hard",
     "question": "2nd/3rd/4th harmonic per staircase level for Tracing Drive 0.1, 1 (0.5 default), band at 200 Hz and 5 kHz, Width 0.1 and 3, Hard",
     "base": TRACING,
     "cases": [["drive-0.1", {"Tracing Drive": {"display": 0.1}}], ["drive-1", {"Tracing Drive": {"display": 1.0}}],
               ["freq-200", {"Tracing Freq.": {"display": 200}}], ["freq-5000", {"Tracing Freq.": {"display": 5000}}],
               ["width-0.1", {"Tracing Width": {"display": 0.1}}], ["width-3", {"Tracing Width": {"display": 3}}],
               ["hard", {"Pinch Soft On": {"item": "Hard"}}]]},

    {"name": "vinyl-distortion-pinch", "plan": "3, 4, 6", "probe": "gap2", "read": ["static", "raw render (L/R harmonic phase)"], "priority": 1,
     "why": "Pinch's odd harmonics: amount against Drive, level, band Freq and Width; opposite sign in L and R in Stereo, equal in Mono; Soft against Hard",
     "question": "odd harmonics per staircase level and the L/R phase of the 3rd harmonic for Pinch Drive 0.1, 1 (0.5 default), band at 200 Hz and 5 kHz, Width 0.1, Mono, Hard",
     "base": PINCH,
     "cases": [["drive-0.1", {"Pinch Drive": {"display": 0.1}}], ["drive-1", {"Pinch Drive": {"display": 1.0}}],
               ["freq-200", {"Pinch Freq.": {"display": 200}}], ["freq-5000", {"Pinch Freq.": {"display": 5000}}],
               ["width-0.1", {"Pinch Width": {"display": 0.1}}], ["mono", {"Pinch Mono On": {"item": "Mono"}}],
               ["hard", {"Pinch Soft On": {"item": "Hard"}}]]},

    {"name": "vinyl-distortion-crackle", "plan": "7", "probe": "gap2", "read": ["silence", "raw render (click counts in the quiet gaps)"], "priority": 2,
     "why": "the Crackle generator: click rate against Density, level against Volume, click shape and spectrum, stereo correlation",
     "question": "clicks per second and amplitude in the quiet gaps for Volume 0.1, 0.5, 1 at Density 10, and Density 1, 25, 50 at Volume 0.5; both models at Drive 0",
     "base": {"Tracing Drive": {"display": 0}, "Pinch Drive": {"display": 0}, "Crackle Volume": {"display": 0.5},
              "Crackle Density": {"display": 10}},
     "cases": [["vol-0.1", {"Crackle Volume": {"display": 0.1}}], ["vol-1", {"Crackle Volume": {"display": 1.0}}],
               ["dens-1", {"Crackle Density": {"display": 1}}], ["dens-25", {"Crackle Density": {"display": 25}}],
               ["dens-50", {"Crackle Density": {"display": 50}}]]},

    {"name": "vinyl-distortion-global-drive", "plan": "5, 8", "probe": "gap2", "read": ["static", "response", "impulse"], "priority": 2,
     "why": "Global Drive as a scaling of the distortion or a wet/dry mix; transparency and latency with both models' Drive at 0",
     "question": "dry level and distortion per staircase level for Global Drive 0, 0.25, 0.5, 1 with both models at 0.5 on 1 kHz bands; sweep and impulse with both Drives at 0",
     "base": {"Tracing On": ON, "Pinch On": ON, "Tracing Drive": {"display": 0.5}, "Pinch Drive": {"display": 0.5},
              "Tracing Freq.": {"display": 1000}, "Pinch Freq.": {"display": 1000}, "Crackle Volume": {"display": 0}},
     "cases": [["global-0", {"Global Drive": {"display": 0}}], ["global-0.25", {"Global Drive": {"display": 0.25}}],
               ["global-0.5", {"Global Drive": {"display": 0.5}}],
               ["drives-0", {"Tracing Drive": {"display": 0}, "Pinch Drive": {"display": 0}}]]},

    # ---- third set (measurements/third/)
    {"name": "vinyl-distortion-band", "plan": "2, 4", "probe": "ext", "read": ["ext: stair100, tone3k, tone10k", "impulse"], "priority": 2,
     "why": "Tracing at 100 Hz and 3 kHz with its band on the tone, the band's colouring at Drive 0, and distortion against tone frequency at a fixed band (the 3 and 10 kHz sines)",
     "question": "100 Hz staircase with the band at 100 Hz; 3 kHz sine with the band at 3 kHz; Drive 0 (impulse); band at 1 kHz with Drive 1",
     "base": TRACING,
     "cases": [["band100", {"Tracing Freq.": {"display": 100}, "Tracing Drive": {"display": 1}}],
               ["band3k", {"Tracing Freq.": {"display": 3000}, "Tracing Drive": {"display": 1}}],
               ["drive0", {"Tracing Drive": {"display": 0}}], ["band1k-drive1", {"Tracing Drive": {"display": 1}}]]},

    {"name": "vinyl-distortion-crackle-repeat", "plan": "7", "probe": "gap2", "read": ["silence and every gap (click times)"], "priority": 2,
     "why": "whether two devices crackle alike (a fixed seed), and whether Global Drive changes the crackle",
     "question": "click times over the whole render at Density 10, Volume 0.5 on two tracks (an unused setting differs), and at Global Drive 0",
     "base": {"Tracing On": OFF, "Pinch On": OFF, "Crackle Density": 10, "Crackle Volume": {"display": 0.5}, "Global Drive": {"display": 1}},
     "cases": [["a", {}], ["b", {"Tracing Freq.": {"display": 2000}}], ["drive0", {"Global Drive": {"display": 0}}]]},
]
