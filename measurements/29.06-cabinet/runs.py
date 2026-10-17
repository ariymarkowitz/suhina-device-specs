# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Cabinet behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.06-cabinet.md > Measurement plan.

Not taken: the full 5 x 3 x 2 = 30 response grid of step 1 (the runs below take every Speaker
at one setting, every Microphone and type at one Speaker, and a few crossings that test whether
the responses multiply), linearity at several sweep levels (the probe's sweep is at one level;
the staircase of cabinet-linearity stands in), pink-noise loudness of step 6 (the `noise`
segment's level gives it), and switching while playing."""

DEVICE = "Cabinet"

BASE = {"Cabinet Type": {"item": "1x12"}, "Microphone Position": {"item": "Near On-Axis"},
        "Microphone Type": {"item": "Condenser"}, "Dual Mono": {"item": "Off"},
        "Dry/Wet": {"display": 100}}

SPEAKERS = ["1x12", "2x12", "4x12", "4x10", "4x10 Bass"]
POSITIONS = ["Near On-Axis", "Near Off-Axis", "Far"]


def cfg(speaker, pos, mic):
    return {"Cabinet Type": {"item": speaker}, "Microphone Position": {"item": pos},
            "Microphone Type": {"item": mic}}


def slug(s):
    return s.lower().replace(" ", "-")


RUNS = [
    {"name": "cabinet-speaker", "plan": "1", "probe": "gap2", "read": ["response", "impulse"],
     "priority": 1,
     "why": "magnitude response and impulse response of each of the five speaker cabinets",
     "question": "sweep response and impulse of every Cabinet Type, Near On-Axis, Condenser",
     "base": BASE,
     "cases": [[f"spk-{slug(s)}", {"Cabinet Type": {"item": s}}] for s in SPEAKERS]},

    {"name": "cabinet-mic", "plan": "1", "probe": "gap2", "read": ["response", "impulse"],
     "priority": 1,
     "why": "what each Microphone position and type does to the response, and the room tail of Far",
     "question": "sweep response and impulse for the three positions with Condenser and Dynamic, 4x12",
     "base": dict(BASE, **{"Cabinet Type": {"item": "4x12"}}),
     "cases": [[f"{slug(p)}-{slug(m)}", {"Microphone Position": {"item": p}, "Microphone Type": {"item": m}}]
               for m in ("Condenser", "Dynamic") for p in POSITIONS]},

    {"name": "cabinet-product", "plan": "1", "probe": "gap2", "read": ["response", "impulse"],
     "priority": 2,
     "why": "whether the response is speaker x position x type (each factor separable) or a separate response per combination",
     "question": "sweep and impulse of crossings that cabinet-speaker and cabinet-mic did not take: 1x12 and 4x10 Bass with the other positions and Dynamic",
     "base": BASE,
     "cases": [["1x12-far-dynamic", cfg("1x12", "Far", "Dynamic")],
               ["1x12-off-condenser", cfg("1x12", "Near Off-Axis", "Condenser")],
               ["bass-on-dynamic", cfg("4x10 Bass", "Near On-Axis", "Dynamic")],
               ["bass-far-condenser", cfg("4x10 Bass", "Far", "Condenser")],
               ["bass-off-dynamic", cfg("4x10 Bass", "Near Off-Axis", "Dynamic")],
               ["2x12-far-dynamic", cfg("2x12", "Far", "Dynamic")]]},

    {"name": "cabinet-linearity", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "whether the speaker or microphone adds distortion or compression at high level (THD and gain across -60 to 0 dBFS)",
     "question": "static curve (gain and THD vs level) for a small, a large and a bass cabinet, Dynamic and Condenser",
     "base": BASE,
     "cases": [["lin-1x12-condenser", cfg("1x12", "Near On-Axis", "Condenser")],
               ["lin-1x12-dynamic", cfg("1x12", "Near On-Axis", "Dynamic")],
               ["lin-4x12-dynamic", cfg("4x12", "Near On-Axis", "Dynamic")],
               ["lin-bass-far", cfg("4x10 Bass", "Far", "Condenser")]]},

    {"name": "cabinet-dual-mono", "plan": "3", "probe": "gap2", "read": ["stereo", "impulse", "response"],
     "priority": 2,
     "why": "Mono vs Dual: left/right levels for one-sided input and whether Dual decorrelates the channels (Far)",
     "question": "2x2 level matrix, impulse L/R taps and sweep L/R of Mono and Dual, for On-Axis and Far",
     "base": dict(BASE, **{"Cabinet Type": {"item": "2x12"}}),
     "cases": [["mono-on", {"Dual Mono": {"item": "Off"}}],
               ["dual-on", {"Dual Mono": {"item": "On"}}],
               ["mono-far", {"Dual Mono": {"item": "Off"}, "Microphone Position": {"item": "Far"}}],
               ["dual-far", {"Dual Mono": {"item": "On"}, "Microphone Position": {"item": "Far"}}]]},

    {"name": "cabinet-drywet", "plan": "5", "probe": "gap2", "read": ["impulse", "response"],
     "priority": 3,
     "why": "Dry/Wet law and whether the dry path is delayed to match the cabinet's latency",
     "question": "impulse taps and sweep at Dry/Wet 0, 25, 50, 75 % (100 % is the default)",
     "base": dict(BASE, **{"Cabinet Type": {"item": "4x12"}}),
     "cases": [[f"wet-{w}", {"Dry/Wet": {"display": w}}] for w in (0, 25, 50, 75)]},
]
