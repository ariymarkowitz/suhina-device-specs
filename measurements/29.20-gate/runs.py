# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Gate behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.20-gate.md > Measurement plan.

The base is the plainest gate: Threshold -18 dB, Return 0, fastest Attack, Hold and Release, Floor
-inf, Lookahead 0, Normal. The probe's staircase (rising 1 kHz sine, -60 to 0 dBFS) shows where the
gate opens, and its bursts (-30, -6, -30 dBFS, 1 s each) open and close it once, so `dynamics`
and the burst waveform give Attack, Hold, Release and the Return window.

Not measurable this way: plan 2's slow up-and-down ramp (the staircase only rises; the close level
is found with the bursts in gate-return), 6 (re-trigger during release needs two close bursts),
9 (burst length against the open decision), 11 (side-chain: no external input), 12 (other sample
rates), and plan 10's per-channel levels are only partly covered by the left / right segments
read from any case."""

DEVICE = "Gate"

BASE = {"Threshold": {"display": -18}, "Return": {"display": 0}, "Attack": {"display": 0.00002},
        "Hold": {"display": 0.001}, "Release": {"display": 0.0001}, "Floor": -75,
        "LookAhead": {"item": "0 ms"}, "FlipMode": {"item": "Normal"}}


def ms(v):
    return {"display": v / 1000}


RUNS = [
    {"name": "gate-threshold-floor", "plan": "2,3", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the level at which the gate opens against Threshold (and what the detector measures), and the closed gain against Floor",
     "question": "Threshold -45, -33, -21 and -9 dB with Floor -inf; and Floor -24, -12, -6 and 0 dB at Threshold -21",
     "base": BASE,
     "cases": [[f"thr{v}", {"Threshold": {"display": v}}] for v in (-45, -33, -21, -9)] + [
         [f"floor{v}", {"Threshold": {"display": -21}, "Floor": {"display": v}}] for v in (-24, -12, -6, 0)]},

    {"name": "gate-return", "plan": "2", "probe": "gap2", "read": ["dynamics", "static"], "priority": 1,
     "why": "the hysteresis rule: whether the gate closes at Threshold - Return, from which -30 dB burst stays open after the -6 dB one",
     "question": "Threshold -24 dB, Return 0 (the default case), 4, 6, 8, 12 and 24 dB: does the third (-30 dBFS) burst pass or stay closed",
     "base": BASE | {"Threshold": {"display": -24}},
     "cases": [[f"ret-{v}", {"Return": {"display": v}}] for v in (4, 6, 8, 12, 24)]},

    {"name": "gate-attack-release", "plan": "4", "probe": "gap2", "read": ["dynamics"], "priority": 1,
     "why": "Attack and Release times against their knobs and the gain curve (linear or exponential) of the opening and closing",
     "question": "Attack 1, 10, 50 and 150 ms; Release 10, 50, 200 and 500 ms (the others at their fastest; the third burst lasts 1 s)",
     "base": BASE,
     "cases": [[f"att-{v}", {"Attack": ms(v)}] for v in (1, 10, 50, 150)] +
              [[f"rel-{v}", {"Release": ms(v)}] for v in (10, 50, 200, 500)]},

    {"name": "gate-hold", "plan": "5", "probe": "gap2", "read": ["dynamics", "bursts waveform"], "priority": 2,
     "why": "Hold: the time between the level dropping under the threshold and the gain starting to fall",
     "question": "Hold 50, 200 and 500 ms with Release 20 ms (the default case has Hold 1 ms)",
     "base": BASE | {"Release": ms(20)},
     "cases": [[f"hold-{v}", {"Hold": ms(v)}] for v in (50, 200, 500)]},

    {"name": "gate-lookahead", "plan": "8", "probe": "gap2", "read": ["impulse", "dynamics"], "priority": 2,
     "why": "latency per Lookahead step and whether a slow Attack with Lookahead lets the transient through",
     "question": "Lookahead 0, 1.5 and 10 ms (impulse delay); with Attack 50 ms at 0 and 10 ms Lookahead",
     "base": BASE,
     "cases": [
         ["la-1.5", {"LookAhead": {"item": "1.5 ms"}}],
         ["la-10", {"LookAhead": {"item": "10 ms"}}],
         ["la-0-att50", {"Attack": ms(50)}],
         ["la-10-att50", {"LookAhead": {"item": "10 ms"}, "Attack": ms(50)}],
     ]},

    {"name": "gate-flip", "plan": "7", "probe": "gap2", "read": ["static", "dynamics"], "priority": 2,
     "why": "Flip: which of Attack and Release applies to which transition, the pass level, and the Floor in Flip",
     "question": "Flip on with fastest times; with Attack 100 ms; with Release 100 ms; with Floor -12 dB",
     "base": BASE | {"FlipMode": {"item": "Flip"}},
     "cases": [
         ["flip-att100", {"Attack": ms(100)}],
         ["flip-rel100", {"Release": ms(100)}],
         ["flip-floor-12", {"Floor": {"display": -12}}],
     ]},

    # ---- third set (measurements/third/). The extended probe's 10 dB/s ramp (1 kHz, -60 to 0
    # dBFS and back) gives the opening and closing levels without the staircase's 3 dB steps; its
    # short bursts (1 to 300 ms at -6 dBFS) test the detector; its split tone (left -6, right
    # -18 dBFS) the linking. The side-chain run plays key-duck on a key track.
    {"name": "gate-ramp", "plan": "2", "probe": "ext", "read": ["ext: ramp (envelope)"], "priority": 1,
     "why": "the open and close levels on a slow ramp for Return 0, 6, 12, 24 dB",
     "question": "level of the ramp where the gate opens (rising) and closes (falling), Threshold -30 dB, fastest times, Floor -75 dB",
     "base": dict(BASE, **{"Threshold": {"display": -30}}),
     "cases": [[f"return-{r}", {"Return": {"display": r}}] for r in (0, 6, 12, 24)]},

    {"name": "gate-detector-retrigger", "plan": "6, 9", "probe": "ext", "read": ["ext: shortbursts, impulsetrain, bedbursts"], "priority": 1,
     "why": "whether short bursts open the gate (peak or RMS detection), and how a burst inside a long release re-opens it",
     "question": "which of the 1 to 300 ms bursts at -6 dBFS open the gate at Threshold -9 and -12 dB; with Release 1.5 s the second burst during the release (Attack 0.02 and 20 ms)",
     "base": BASE,
     "cases": [["thr-9", {"Threshold": {"display": -9}}], ["thr-12", {"Threshold": {"display": -12}}],
               ["release-1.5-fast", {"Threshold": {"display": -12}, "Release": {"display": 1.5}}],
               ["release-1.5-attack20", {"Threshold": {"display": -12}, "Release": {"display": 1.5}, "Attack": {"display": 0.02}}]]},

    {"name": "gate-stereo", "plan": "10", "probe": "ext", "read": ["ext: lrsplit, side"], "priority": 2,
     "why": "linking: does the quiet channel open with the loud one",
     "question": "per-channel gain of the split tone (left -6, right -18 dBFS) at Threshold -12 dB, and of side-only noise at Threshold -24 dB",
     "base": BASE,
     "cases": [["thr-12", {"Threshold": {"display": -12}}], ["thr-24", {"Threshold": {"display": -24}}]]},

    {"name": "gate-sidechain", "plan": "11", "probe": "gap2", "read": ["envelope of the steady tone under the key bursts", "response (Listen)"], "priority": 1,
     "why": "the external side-chain: opening by the key's level, S/C Gain, S/C Mix, and the S/C EQ heard through Listen",
     "question": "the steady tone under key-duck's bursts (-36 to 0 dBFS), Threshold -20 dB: S/C Gain 0, +12 dB, S/C Mix 50 %; Listen with the EQ off, Bell 1 kHz +12 dB Q 2, Low pass 1 kHz, High pass 1 kHz",
     "base": dict(BASE, **{"Threshold": {"display": -20}, "S/C On": {"item": "On"}, "S/C EQ On": {"item": "Off"},
                           "S/C Gain": {"display": 0}, "S/C Mix": {"display": 100},
                           "@SideChain/RoutedInput/Routable/Target": "key:measurements/probe-keys/key-duck.wav"}),
     "cases": [["sc-gain+12", {"S/C Gain": {"display": 12}}], ["sc-mix-50", {"S/C Mix": {"display": 50}}],
               ["listen-eq-off", {"S/C Listen": {"item": "On"}}]] +
              [[f"listen-{n}", {"S/C Listen": {"item": "On"}, "S/C EQ On": {"item": "On"}, "S/C EQ Type": {"item": t},
                                "S/C EQ Freq": {"display": 1000}, "S/C EQ Q": {"display": q}, "S/C EQ Gain": g}]
               for n, t, q, g in (("bell", "Bell", 2, 12), ("lp", "Low pass", 0.71, 0), ("hp", "High pass", 0.71, 0))]},
]
