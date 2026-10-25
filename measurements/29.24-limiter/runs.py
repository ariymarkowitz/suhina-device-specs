# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Limiter behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.24-limiter.md > Measurement plan.

The probe tops out at 0 dBFS, so the limiter is driven with Input Gain: a staircase of -60 to 0 dBFS
becomes -48 to +12 dB at the limiter with Gain +12. The base is Standard, L/R, Lookahead 3 ms, Link
100 %, Release 100 ms (Auto off), Maximize off, Gain 0, Ceiling -6 dB.

Not measurable this way: plan 9 (Link needs a loud and a quiet channel at once; the probe has the
tone in both channels or in one only) and the M/S link; plan 10's mid-only or side-only signals;
plan 11's inter-sample peak at fs/4 with a 45 degree phase (no such signal; the True Peak case is
only compared on the staircase and the impulse); plan 5's other sample rates and the title-bar
tooltip; plan 8's drum loop and single clicks (only the 1 s bursts); the 60 Hz tone."""

DEVICE = "Limiter"

BASE = {"Input Gain": {"display": 0}, "Ceiling": {"display": -6}, "Release": {"display": 0.1},
        "Auto": {"item": "Off"}, "Link": {"display": 100}, "M/S Link": {"display": 0},
        "Lookahead": {"item": "3 ms"}, "Routing": {"item": "L/R"}, "Mode": {"item": "Standard"},
        "Maximize On": {"item": "Off"}}
GAIN12 = {"Input Gain": {"display": 12}}

RUNS = [
    {"name": "limiter-static", "plan": "2,3", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the limiting curve: the ceiling actually reached (offset), overshoot near the knee, and that Gain is a pre-gain before the limiter",
     "question": "staircase with Ceiling -6 dB at Gain 0 (the default case), Gain +12 and +24 dB; Ceiling -12 and -1 dB at Gain +12",
     "base": BASE,
     "cases": [
         ["gain12", GAIN12],
         ["gain24", {"Input Gain": {"display": 24}}],
         ["gain12-ceil-12", GAIN12 | {"Ceiling": {"display": -12}}],
         ["gain12-ceil-1", GAIN12 | {"Ceiling": {"display": -1}}],
         ["gain-12-ceil-1", {"Input Gain": {"display": -12}, "Ceiling": {"display": -1}}],
     ]},

    {"name": "limiter-maximize", "plan": "4", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "Maximize: the makeup added for each Threshold, and how Output sets the ceiling",
     "question": "Maximize on, Output 0 dB, Threshold -3, -6, -12 and -24 dB; Output -6 dB at Threshold -6 and -12 dB at Threshold -12",
     "base": BASE | {"Maximize On": {"item": "On"}, "Output": {"display": 0}},
     "cases": [[f"thr{v}", {"Threshold": {"display": v}}] for v in (-3, -6, -12, -24)] + [
         ["thr-6-out-6", {"Threshold": {"display": -6}, "Output": {"display": -6}}],
         ["thr-12-out-12", {"Threshold": {"display": -12}, "Output": {"display": -12}}],
     ]},

    {"name": "limiter-release", "plan": "7,8", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "Release as a gain-recovery curve (time constant against the knob), and what Auto does on a 1 s limited burst",
     "question": "bursts -30, -6, -30 dBFS with Gain +12 and Ceiling -6 dB (12 dB of limiting in the middle burst): Release 1, 10, 300 and 1000 ms, and Auto",
     "base": BASE | GAIN12,
     "cases": [[f"rel-{v}ms", {"Release": {"display": v / 1000}}] for v in (1, 10, 300, 1000)] + [
         ["auto", {"Auto": {"item": "On"}}]],
    },

    {"name": "limiter-lookahead-modes", "plan": "5,6,11", "probe": "gap2", "read": ["impulse", "dynamics", "static"], "priority": 2,
     "why": "latency per Lookahead step and per Ceiling Mode and Routing, the attack through the lookahead, and the Soft Clip and True Peak curves",
     "question": "Lookahead 1.5 and 6 ms (3 ms is the default case), Soft Clip, True Peak and M/S routing, all with Gain +12 and Ceiling -6 dB",
     "base": BASE | GAIN12,
     "cases": [
         ["la-1.5", {"Lookahead": {"item": "1.5 ms"}}],
         ["la-6", {"Lookahead": {"item": "6 ms"}}],
         ["soft-clip", {"Mode": {"item": "Soft Clip"}}],
         ["true-peak", {"Mode": {"item": "True Peak"}}],
         ["ms", {"Routing": {"item": "M/S"}}],
     ]},

    # ---- third set (measurements/third/): the extended probe (bursts over a bed, split tone, mid
    # and side noise, 10 and 15 kHz sines, the 10 dB/s ramp)
    {"name": "limiter-auto-release-bursts", "plan": "8", "probe": "ext", "read": ["ext: bedbursts envelope"], "priority": 1,
     "why": "Auto release after a click, a 100 ms burst and 3 s of limiting, and whether the Release knob still acts with Auto on",
     "question": "gain over the -30 dBFS bed after each bed burst (18 dB over a -24 dB ceiling): Auto on with Release 10 ms and 1 s; Auto off at 300 ms",
     "base": dict(BASE, **{"Ceiling": {"display": -24}}),
     "cases": [["auto-rel10", {"Auto": {"item": "On"}, "Release": {"display": 0.01}}],
               ["auto-rel1000", {"Auto": {"item": "On"}, "Release": {"display": 1}}],
               ["manual-300", {"Release": {"display": 0.3}}]]},

    {"name": "limiter-link-routing", "plan": "9, 10", "probe": "ext", "read": ["ext: lrsplit, mid, side"], "priority": 1,
     "why": "the Link law (gain on the quiet channel) in L/R, M/S Link in M/S, and which of mid and side is limited",
     "question": "per-channel gain of the split tone (left 6 dB over, right 6 dB under a -12 dB ceiling) at Link 0, 25, 50, 75, 100 %; mid and side noise at a -24 dB ceiling in M/S with M/S Link 0, 50, 100 %",
     "base": dict(BASE, **{"Ceiling": {"display": -12}}),
     "cases": [[f"link-{l}", {"Link": {"display": l}}] for l in (0, 25, 50, 75)] +
              [[f"ms-link-{l}", {"Routing": {"item": "M/S"}, "Ceiling": {"display": -24}, "M/S Link": {"display": l}}] for l in (0, 50, 100)]},

    {"name": "limiter-ceiling-modes", "plan": "11, 12", "probe": "ext", "read": ["ext: tone10k, tone15k (sample and 8x peaks), ramp"], "priority": 2,
     "why": "inter-sample peaks in Standard against True Peak, the Soft Clip curve in fine steps, and the dry path under the ceiling",
     "question": "sample and reconstructed peaks of the 10 and 15 kHz sines at Input Gain +6 dB, Ceiling -1 dB, each Mode; the ramp in Soft Clip at Input Gain +6 dB; Input Gain -6 dB under a 0 dB ceiling (Maximize off)",
     "base": dict(BASE, **{"Ceiling": {"display": -1}, "Input Gain": {"display": 6}}),
     "cases": [[m.lower().replace(" ", "-"), {"Mode": {"item": m}}] for m in ("Standard", "Soft Clip", "True Peak")] +
              [["dry-under-ceiling", {"Ceiling": {"display": 0}, "Input Gain": {"display": -6}}]]},
]
