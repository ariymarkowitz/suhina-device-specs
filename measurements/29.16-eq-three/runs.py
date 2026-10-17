# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""EQ Three behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.16-eq-three.md > Measurement plan.

All runs read `response.sweep_db` (time-invariant) and the impulse taps (phase / flatness of the
band sum). Band gains of -inf are set with norm 0.

Not measurable this way: plan 5's kill-button click (needs a change during the render); 6 (the
LEDs are GUI only); 7 (latency is read from the impulse of any case, no extra run needed);
8 (what the display shows for FreqLo above FreqHi; the crossed-over audio is run in eq-three-freq)."""

DEVICE = "EQ Three"

INF = {"norm": 0.0}   # -inf dB
BASE = {"FreqLo": {"display": 500}, "FreqHi": {"display": 2000}, "Slope": {"item": "48"}}

LOW = {"GainMid": INF, "GainHi": INF}
MID = {"GainLo": INF, "GainHi": INF}
HIGH = {"GainLo": INF, "GainMid": INF}

RUNS = [
    {"name": "eq-three-bands", "plan": "2,3,4", "probe": "gap2", "read": ["response.sweep_db", "impulse"], "priority": 1,
     "why": "crossover slope, corner level and phase of each band in 24 and 48 dB mode, and how flat the sum is (the default case is the flat 48 dB sum)",
     "question": "each band alone (the other two at -inf) at crossovers 500 Hz and 2 kHz, in 24 and 48 dB; the flat sum in 24 dB",
     "base": BASE,
     "cases": [
         ["low-48", dict(LOW)],
         ["mid-48", dict(MID)],
         ["high-48", dict(HIGH)],
         ["low-24", LOW | {"Slope": {"item": "24"}}],
         ["mid-24", MID | {"Slope": {"item": "24"}}],
         ["high-24", HIGH | {"Slope": {"item": "24"}}],
         ["flat-24", {"Slope": {"item": "24"}}],
     ]},

    {"name": "eq-three-gain", "plan": "5", "probe": "gap2", "read": ["response.sweep_db", "static"], "priority": 1,
     "why": "the gain law of each band (display dB against real dB, +6 at the top), -inf, and what the kill button does compared with -inf",
     "question": "band gains +6, -6, -20 dB and -inf, one band at a time, and the kill buttons at gain 0",
     "base": BASE | {"Slope": {"item": "24"}},
     "cases": [
         ["mid+6", {"GainMid": {"display": 6}}],
         ["mid-6", {"GainMid": {"display": -6}}],
         ["mid-20", {"GainMid": {"display": -20}}],
         ["mid-inf", {"GainMid": INF}],
         ["low+6-high-6", {"GainLo": {"display": 6}, "GainHi": {"display": -6}}],
         ["low-kill", {"LowOn": {"item": "Off"}}],
         ["mid-kill", {"MidOn": {"item": "Off"}}],
         ["high-kill", {"HighOn": {"item": "Off"}}],
     ]},

    {"name": "eq-three-freq", "plan": "2,8", "probe": "gap2", "read": ["response.sweep_db"], "priority": 2,
     "why": "crossover frequency accuracy over the knobs' range, narrow mid band, and what the audio does when FreqLo is above FreqHi",
     "question": "low band alone at FreqLo 50 Hz and 5 kHz, high band alone at FreqHi 200 Hz and 18 kHz, a narrow mid band, and FreqLo above FreqHi",
     "base": BASE | {"Slope": {"item": "24"}},
     "cases": [
         ["low-50", LOW | {"FreqLo": {"display": 50}}],
         ["low-5k", LOW | {"FreqLo": {"display": 5000}}],
         ["high-200", HIGH | {"FreqHi": {"display": 200}}],
         ["high-18k", HIGH | {"FreqHi": {"display": 18000}}],
         ["mid-narrow", MID | {"FreqLo": {"display": 1000}, "FreqHi": {"display": 1100}}],
         ["crossed-mid", MID | {"FreqLo": {"display": 3000}, "FreqHi": {"display": 500}}],
         ["crossed-flat", {"FreqLo": {"display": 3000}, "FreqHi": {"display": 500}}],
     ]},
]
