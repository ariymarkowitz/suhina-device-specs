# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Erosion behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.17-erosion.md > Measurement plan.

Erosion is a modulated delay, so the useful readings are the steady 1 kHz tone's FM depth and
sidebands (`modulation`, and a spectrum of the steady segment read from the render), the
impulse (base delay) and the L/R correlation. Stereo Width is 0 in the base so one modulator
serves both channels, except in erosion-stereo.

Not measurable this way: plan 8 (Alt-drag is GUI only); the legacy Erosion Legacy device (a
different device); plan 7 (dry/wet) is answered by erosion-amount's Amount 0 against bypass."""

DEVICE = "Erosion"

BASE = {"Amount": {"display": 50}, "Frequency": {"display": 500}, "Noise Blend": {"display": 0},
        "Filter Width": {"display": 1.0}, "Stereo Width": {"display": 0}}

RUNS = [
    {"name": "erosion-amount", "plan": "1,2,7", "probe": "gap2", "read": ["modulation", "impulse"], "priority": 1,
     "why": "Amount's law: the delay excursion (from the FM depth in cents) against Amount and Freq, and the base delay at Amount 0",
     "question": "sine modulator only, Amount 0 to 100 % at Freq 500 Hz (the default case is Amount 50 %), and Freq 20 Hz and 5 kHz",
     "base": BASE,
     "cases": [
         ["amt-0", {"Amount": {"display": 0}}],
         ["amt-25", {"Amount": {"display": 25}}],
         ["amt-100", {"Amount": {"display": 100}}],
         ["f20-amt-100", {"Frequency": {"display": 20}, "Amount": {"display": 100}}],
         ["f5k-amt-50", {"Frequency": {"display": 5000}}],
         ["f5k-amt-100", {"Frequency": {"display": 5000}, "Amount": {"display": 100}}],
     ]},

    {"name": "erosion-noise", "plan": "4", "probe": "gap2", "read": ["modulation", "steady spectrum"], "priority": 2,
     "why": "the noise modulator: sideband centre and bandwidth against Freq and Filter Width (and its unit and range)",
     "question": "noise modulator only, Amount 50 %, Filter Width 0.1, 1 and 2.5 at Freq 500 Hz, and Freq 100 Hz and 5 kHz at Width 1",
     "base": BASE | {"Noise Blend": {"display": 100}},
     "cases": [
         ["w-0.1", {"Filter Width": {"display": 0.1}}],
         ["w-1", {"Filter Width": {"display": 1.0}}],
         ["w-2.5", {"Filter Width": {"display": 2.5}}],
         ["f100-w-1", {"Frequency": {"display": 100}}],
         ["f5k-w-1", {"Frequency": {"display": 5000}}],
     ]},

    {"name": "erosion-blend", "plan": "5", "probe": "gap2", "read": ["modulation", "steady spectrum"], "priority": 2,
     "why": "the mixing law between the sine and the noise modulator (is Noise Blend an amplitude crossfade?)",
     "question": "Noise Blend 0, 25, 50, 75, 100 % at Amount 50 %, Freq 500 Hz, Filter Width 1",
     "base": BASE,
     "cases": [[f"blend-{v}", {"Noise Blend": {"display": v}}] for v in (0, 25, 50, 75, 100)]},

    {"name": "erosion-stereo", "plan": "6", "probe": "gap2", "read": ["modulation", "stereo"], "priority": 2,
     "why": "how Stereo Width morphs the two channels' modulators, for the sine (phase offset) and the noise (independent sources)",
     "question": "Stereo Width 0 (the default case), 50 and 100 % with the sine modulator and with the noise modulator, Amount 50 %",
     "base": BASE,
     "cases": [
         ["sine-sw-50", {"Stereo Width": {"display": 50}}],
         ["sine-sw-100", {"Stereo Width": {"display": 100}}],
         ["noise-sw-0", {"Noise Blend": {"display": 100}}],
         ["noise-sw-50", {"Noise Blend": {"display": 100}, "Stereo Width": {"display": 50}}],
         ["noise-sw-100", {"Noise Blend": {"display": 100}, "Stereo Width": {"display": 100}}],
     ]},
]
