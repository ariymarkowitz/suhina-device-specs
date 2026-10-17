# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Redux behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.30-redux.md > Measurement plan.

The base is the Redux at its defaults except Dry/Wet 100 %: Rate 40 kHz, Jitter 0, Bits 16, Shape 0,
DC Shift off, Pre and Post filters off, Post-Filter octave 0. The probe has a 1 kHz tone, white noise and
the staircase, so the alias of the tone (steady segment, re-read as a spectrum) gives the true rate, the
staircase's levels and harmonics give the quantizer, and the noise gives the filters.

Not measurable this way: plan 6 (section order needs a 3 kHz tone, the probe has only 1 kHz: order can
be inferred from the filter runs); plan 8 and the eco/high quality of plan 7 (Hi-Quality is a
context-menu option, not a parameter); plan 1's 10 kHz sweep through the rate (the 1 kHz tone at low
rates stands in for it, with the noise for the broadband view); the slow ramp of plan 4 (the 3 dB staircase
of 0.25 s steps and the -12 dBFS tone are used)."""

DEVICE = "Redux"

BASE = {"Sample Rate": {"display": 40000}, "Jitter": {"display": 0}, "Bit Depth": 16,
        "Quantizer Shape": {"display": 0}, "DC Shift": {"item": "Off"},
        "Pre-Filter On": {"item": "Off"}, "Post-Filter On": {"item": "Off"}, "Post-Filter": {"norm": 0.5},
        "Dry/Wet": {"display": 100}}


def rate(v):
    return {"Sample Rate": {"display": v}}


RUNS = [
    {"name": "redux-rate", "plan": "1", "probe": "gap2", "read": ["steady tone spectrum", "impulse", "response.noise_db"], "priority": 1,
     "why": "the true effective sample rate against the Rate control (the 1 kHz tone's alias frequency), non-integer ratios, and the hold length from the impulse",
     "question": "1 kHz tone and noise at Rate 30 kHz, 22.05 kHz, 15 kHz, 8 kHz, 3 kHz, 1.5 kHz and 400 Hz, no filters, 16 bits",
     "base": BASE,
     "cases": [[f"rate-{n}", rate(v)] for n, v in (("30k", 30000), ("22k", 22050), ("15k", 15000), ("8k", 8000),
                                                   ("3k", 3000), ("1.5k", 1500), ("400", 400))]},

    {"name": "redux-bits", "plan": "4", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the quantizer: number of output levels per Bits, the step positions (mid-tread or mid-rise), the noise floor and the 1-bit square",
     "question": "staircase at 1 kHz for Bits 1, 2, 4, 8 and 12 (16 is the default case), Shape 0, DC Shift off",
     "base": BASE,
     "cases": [[f"bits-{b}", {"Bit Depth": b}] for b in (1, 2, 4, 8, 12)]},

    {"name": "redux-shape-dc", "plan": "4,5", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "Shape's morph to the companded quantizer (finer steps at small amplitudes) and what DC Shift does to the quantizer's levels",
     "question": "4 bits at Shape 50 and 100 %; DC Shift on at 2, 4 and 8 bits; DC Shift with Shape 100 % at 4 bits; 2 bits at Shape 50 %",
     "base": BASE | {"Bit Depth": 4},
     "cases": [
         ["b4-shape50", {"Quantizer Shape": {"display": 50}}],
         ["b4-shape100", {"Quantizer Shape": {"display": 100}}],
         ["b2-shape50", {"Bit Depth": 2, "Quantizer Shape": {"display": 50}}],
         ["b2-dc", {"Bit Depth": 2, "DC Shift": {"item": "On"}}],
         ["b4-dc", {"DC Shift": {"item": "On"}}],
         ["b8-dc", {"Bit Depth": 8, "DC Shift": {"item": "On"}}],
         ["b4-dc-shape100", {"DC Shift": {"item": "On"}, "Quantizer Shape": {"display": 100}}],
     ]},

    {"name": "redux-filters", "plan": "3", "probe": "gap2", "read": ["response.noise_db", "response.sweep_db", "steady tone spectrum"], "priority": 1,
     "why": "the Pre and Post low-pass filters: corner against Rate, slope, and the Post-Filter octave scale (-4 to +4) around half the rate",
     "question": "Rate 8 kHz: Pre only, Post only, both; Post at octave +2, -2, +4 and -4 (set by norm 0.75, 0.25, 1, 0; octave 0 is the 'post-only' case)",
     "base": BASE | rate(8000),
     "cases": [
         ["pre", {"Pre-Filter On": {"item": "On"}}],
         ["post", {"Post-Filter On": {"item": "On"}}],
         ["pre-post", {"Pre-Filter On": {"item": "On"}, "Post-Filter On": {"item": "On"}}],
         ["post+2", {"Post-Filter On": {"item": "On"}, "Post-Filter": {"norm": 0.75}}],
         ["post-2", {"Post-Filter On": {"item": "On"}, "Post-Filter": {"norm": 0.25}}],
         ["post+4", {"Post-Filter On": {"item": "On"}, "Post-Filter": {"norm": 1.0}}],
         ["post-4", {"Post-Filter On": {"item": "On"}, "Post-Filter": {"norm": 0.0}}],
     ]},

    {"name": "redux-jitter", "plan": "2", "probe": "gap2", "read": ["steady tone spectrum", "modulation", "response.noise_db", "stereo"], "priority": 2,
     "why": "Jitter's size and law (noise floor around the aliased tone), the decorrelation of the channels, and how the Pre filter reduces it",
     "question": "Rate 8 kHz, Jitter 25, 50 and 100 % (0 % is the default case), and Jitter 100 % with the Pre filter",
     "base": BASE | rate(8000),
     "cases": [
         ["jitter-25", {"Jitter": {"display": 25}}],
         ["jitter-50", {"Jitter": {"display": 50}}],
         ["jitter-100", {"Jitter": {"display": 100}}],
         ["jitter-100-pre", {"Jitter": {"display": 100}, "Pre-Filter On": {"item": "On"}}],
     ]},

    {"name": "redux-drywet", "plan": "7", "probe": "gap2", "read": ["impulse", "static"], "priority": 3,
     "why": "the Dry/Wet law and whether the dry path is aligned with the wet one (a latency-free device shows no comb)",
     "question": "Rate 8 kHz, 8 bits: Dry/Wet 0 and 50 % (100 % is the default case)",
     "base": BASE | rate(8000) | {"Bit Depth": 8},
     "cases": [["dw-0", {"Dry/Wet": {"display": 0}}], ["dw-50", {"Dry/Wet": {"display": 50}}]]},
]
