# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Multiband Dynamics behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.26-multiband-dynamics.md > Measurement plan.

The probe's 1 kHz tone falls in the Mid band at the default crossovers (120 Hz and 2.5 kHz), so
the dynamics runs set the Mid band and leave Low and High at ratio 1. The base is: Peak detector,
Soft Knee off, Mid Above Threshold -30 dB, Mid attack and release at their 0.1 ms minimum, all ratios
1 (so the default case is a crossover with no dynamics), Amount 100 %, Time 100 %. Ratios are set as
API values (Above v: 1:x with x = 1/(1+v); Below v: x = 1/(1-v)).

Solo, the High and Low buttons and the side-chain are not parameters / not possible, so a band is
isolated by pulling the other two bands' Output Gain down 24 dB (the sweep then shows it to about
-24 dB below its peak).

Not measurable this way: plan 3 (latency is read from the impulse of any case, no extra run); 8's
bursts of 1 to 300 ms (the probe's bursts are 1 s: RMS against Peak is compared on the staircase and on the
1 s bursts); 10's solo; 11 and 12 (side-chain); 13 (a Low crossover above the High one is not
a case the API will set: Low-Mid goes to 3 kHz, Mid-High from 300 Hz); 14 (meters)."""

DEVICE = "Multiband Dynamics"

BASE = {
    "Peak/RMS Mode": {"item": "Peak"}, "Soft Knee On/Off": {"item": "Off"},
    "Above Threshold (Mid)": {"display": -30},
    "Attack Time (Mid)": {"display": 0.0001}, "Release Time (Mid)": {"display": 0.0001},
    "Amount": {"display": 100}, "Time Scaling": {"display": 100},
}
MID_ONLY = {"Output Gain (Low)": {"display": -24}, "Output Gain (High)": {"display": -24}}


def above(v):
    return {"Above Ratio (Mid)": v}


def below(v):
    return {"Below Ratio (Mid)": v, "Below Threshold (Mid)": {"display": -30},
            "Above Threshold (Mid)": {"display": 0}}


def xo(lo, hi):
    return {"Low-Mid Crossover": {"display": lo}, "Mid-High Crossover": {"display": hi}}


RUNS = [
    {"name": "multiband-dynamics-crossover", "plan": "2,3", "probe": "gap2", "read": ["response.sweep_db", "impulse"], "priority": 1,
     "why": "the crossover filters: slope and phase of each band, overlap, and how flat the sum of the three bands is",
     "question": "flat sum at 120 Hz / 2.5 kHz (default case), 500 Hz / 2 kHz and 60 Hz / 10 kHz; each band alone (others -24 dB) at 500 Hz / 2 kHz",
     "base": BASE,
     "cases": [
         ["flat-500-2k", xo(500, 2000)],
         ["flat-60-10k", xo(60, 10000)],
         ["low-500", xo(500, 2000) | {"Output Gain (Mid)": {"display": -24}, "Output Gain (High)": {"display": -24}}],
         ["mid-500-2k", xo(500, 2000) | MID_ONLY],
         ["high-2k", xo(500, 2000) | {"Output Gain (Low)": {"display": -24}, "Output Gain (Mid)": {"display": -24}}],
     ]},

    {"name": "multiband-dynamics-above", "plan": "4,5,6,9", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the Above stage: slope per ratio (and expansion), knee width, RMS against Peak, how Amount scales it, and whether Input Gain moves the threshold",
     "question": "Mid band Above Threshold -30 dB: ratios 1:2, 1:4, 1:Inf, 1:0.67; Soft Knee on; RMS; Amount 50 %; Input +12 dB",
     "base": BASE,
     "cases": [
         ["r2", above(-0.5)],
         ["r4", above(-0.75)],
         ["r-inf", above(-1)],
         ["r0.67-expand", above(0.5)],
         ["r4-knee", above(-0.75) | {"Soft Knee On/Off": {"item": "On"}}],
         ["r4-rms", above(-0.75) | {"Peak/RMS Mode": {"item": "RMS"}}],
         ["r4-amount50", above(-0.75) | {"Amount": {"display": 50}}],
         ["r4-input+12", above(-0.75) | {"Input Gain (Mid)": {"display": 12}}],
     ]},

    {"name": "multiband-dynamics-below", "plan": "4,5", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the Below stage: which way each ratio bends the curve (upward compression, downward expansion) and its knee",
     "question": "Mid band Below Threshold -30 dB (Above stage out of the way): ratios 1:2, 1:0.50, 1:0.25, 1:Inf; Soft Knee on at 1:2",
     "base": BASE,
     "cases": [
         ["b2", below(0.5)],
         ["b0.5", below(-1)],
         ["b0.25", below(-3)],
         ["b-inf", below(1)],
         ["b2-knee", below(0.5) | {"Soft Knee On/Off": {"item": "On"}}],
     ]},

    {"name": "multiband-dynamics-time", "plan": "6,7", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "Attack and Release as times of the Above stage (63 % and 10-90 %), and the Time scaling factor",
     "question": "bursts -30, -6, -30 dBFS Above Threshold -20 dB, ratio 1:4: Mid Attack 1, 10, 100 ms; Release 10, 100, 500 ms; and Time 10, 100 and 316 % with Attack and Release 100 ms",
     "base": BASE | above(-0.75) | {"Above Threshold (Mid)": {"display": -20}},
     "cases": [[f"att-{v}ms", {"Attack Time (Mid)": {"display": v / 1000}}] for v in (1, 10, 100)]
              + [[f"rel-{v}ms", {"Release Time (Mid)": {"display": v / 1000}}] for v in (10, 100, 500)]
              + [[f"time-{p}", {"Attack Time (Mid)": {"display": 0.1}, "Release Time (Mid)": {"display": 0.1},
                                "Time Scaling": {"display": p}}] for p in (10, 100, 316)]},

    {"name": "multiband-dynamics-bands", "plan": "4,10", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "that each band has its own detector and settings: the same tone compressed in the Low and High band, and a neighbour band's compression leaving it alone",
     "question": "1 kHz tone put in the Low band (crossovers 3 kHz / 10 kHz) and High band (30 Hz / 300 Hz) with that band at 1:4; Low band at 1:4 with the tone in Mid; Mid band activator off at 1:4",
     "base": BASE,
     "cases": [
         ["tone-in-low", xo(3000, 10000) | {"Above Threshold (Low)": {"display": -30}, "Above Ratio (Low)": -0.75,
                                           "Attack Time (Low)": {"display": 0.0001}, "Release Time (Low)": {"display": 0.0001}}],
         ["tone-in-high", xo(30, 300) | {"Above Threshold (High)": {"display": -30}, "Above Ratio (High)": -0.75,
                                        "Attack Time (High)": {"display": 0.0001}, "Release Time (High)": {"display": 0.0001}}],
         ["neighbour-low-r4", {"Above Threshold (Low)": {"display": -30}, "Above Ratio (Low)": -0.75}],
         ["mid-off-r4", above(-0.75) | {"Band Activator (Mid)": {"item": "Off"}}],
     ]},
]
