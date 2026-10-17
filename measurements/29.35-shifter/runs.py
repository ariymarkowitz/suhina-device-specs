# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shifter behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.35-shifter.md › Measurement plan.

Output frequencies are read from the renders (the 8 s steady 1 kHz tone, spectrum or zero-crossing
frequency), which analyse.py does not do for a shifter; `read` says so per run.

Left out (cannot be measured this way): Spread (not an API parameter) and so Wide; MIDI mode and
Glide (no MIDI input); the LFO's stereo and shape-warp controls (Phase, Spin, Width, Offset, Duty
Cycle), which come after the basic LFO run if its result calls for them; the Window's effect on a
click or a low tone beyond what the pitch runs show; changes during the render.
"""

DEVICE = "Shifter"

ON, OFF = 1, 0
# Pitch mode, nothing modulating, no delay, wet only.
BASE = {"Mode": {"item": "Pitch"}, "Pitch Coarse": 0, "Pitch Fine": {"display": 0}, "Dry/Wet": {"display": 100},
        "Delay On": OFF, "Lfo Amount St": {"display": 0}, "Lfo Amount Hz": {"display": 0}, "Env On": OFF}
FREQ = {**BASE, "Mode": {"item": "Freq"}}
RING = {**BASE, "Mode": {"item": "Ring"}}
# Delay alone: free time, no shift, 50 % feedback.
DELAY = {**BASE, "Delay On": ON, "Delay Sync": OFF, "Delay Time": {"display": 0.25},
         "Delay Feedback": {"display": 50}}

RUNS = [
    {"name": "shifter-pitch-accuracy", "plan": "2", "probe": "gap2", "read": ["impulse", "steady (output frequency)"], "priority": 1,
     "why": "the Pitch mode ratio over the whole Coarse range, and the latency (the default case is 0 st)",
     "question": "output frequency of the 1 kHz tone for Coarse -24, -12, -5, +7, +12, +24 st (Window 80 ms); impulse delay at 0 st",
     "base": BASE,
     "cases": [[f"coarse{c:+d}", {"Pitch Coarse": c}] for c in (-24, -12, -5, 7, 12, 24)]},

    {"name": "shifter-freq", "plan": "4", "probe": "gap2", "read": ["steady (spectrum)"], "priority": 1,
     "why": "Freq mode is a single-sideband shift: output frequency, sideband rejection, behaviour past 0 Hz, and the Fine range",
     "question": "spectrum of the 1 kHz tone shifted by Coarse -1200, -100, -10, +10, +100, +1000 Hz and Fine +2 Hz",
     "base": FREQ,
     "cases": [[f"fshift{c:+d}", {"FShift Coarse": {"display": c}}] for c in (-1200, -100, -10, 10, 100, 1000)]
     + [["fine+2", {"Mod Fine": {"display": 2}}]]},

    {"name": "shifter-ring", "plan": "5", "probe": "gap2", "read": ["steady (spectrum)", "static"], "priority": 1,
     "why": "Ring mode: sideband levels, carrier leakage, and where Drive sits (before or after the multiplication)",
     "question": "spectrum of the 1 kHz tone for carrier 100, 440, 5000 Hz (default 1 kHz is the default case); staircase harmonics for Drive on at 0, 12, 24 dB at 440 Hz",
     "base": RING,
     "cases": [["ring-100", {"RM Coarse": {"display": 100}}], ["ring-440", {"RM Coarse": {"display": 440}}],
               ["ring-5000", {"RM Coarse": {"display": 5000}}]]
     + [[f"drive-{g}", {"RM Coarse": {"display": 440}, "RM Drive": ON, "RM Drive Gain": {"display": g}}]
        for g in (0, 12, 24)]},

    {"name": "shifter-delay-timing", "plan": "7", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "delay time (free and synced), feedback per repeat, Tone's low-pass, and whether the dry is delayed at 50 %",
     "question": "echo times and levels of an impulse (Pitch 0 st): Time 100 ms and 1 s, Sync 1/8, Feedback 25 and 100 %, Tone 1 kHz, Dry/Wet 50 % (default: 250 ms, 50 %)",
     "base": DELAY,
     "cases": [["t-100ms", {"Delay Time": {"display": 0.1}}], ["t-1000ms", {"Delay Time": {"display": 1.0}}],
               ["sync-1/8", {"Delay Sync": ON, "Delay Synced": 6}],
               ["fb-25", {"Delay Feedback": {"display": 25}}], ["fb-100", {"Delay Feedback": {"display": 100}}],
               ["tone-1k", {"Tone": {"display": 1000}}], ["dw-50", {"Dry/Wet": {"display": 50}}]]},

    {"name": "shifter-delay-loop", "plan": "7", "probe": "gap2", "read": ["steady (spectrum over time)"], "priority": 2,
     "why": "whether the shift is applied again on every repeat (the shifter inside the feedback loop) in each mode",
     "question": "frequency of the 1 kHz tone in each 1 s repeat with Delay 1 s, Feedback 70 %: Freq +-100 Hz, Pitch +-12 st",
     "base": {**DELAY, "Delay Time": {"display": 1.0}, "Delay Feedback": {"display": 70}},
     "cases": [["loop-freq+100", {"Mode": {"item": "Freq"}, "FShift Coarse": {"display": 100}}],
               ["loop-freq-100", {"Mode": {"item": "Freq"}, "FShift Coarse": {"display": -100}}],
               ["loop-pitch+12", {"Pitch Coarse": 12}], ["loop-pitch-12", {"Pitch Coarse": -12}]]},

    {"name": "shifter-pitch-window", "plan": "2, 3, 11", "probe": "gap2", "read": ["impulse", "steady (modulation)"], "priority": 2,
     "why": "Window's effect on latency and artefacts, Fine in cents, and the Dry/Wet law with a shifted wet",
     "question": "latency and AM of the +7 st tone for Window 10, 30, 200, 350 ms; Fine +50, +100, -100 ct; Dry/Wet 50 %",
     "base": {**BASE, "Pitch Coarse": 7},
     "cases": [[f"win-{w}ms", {"Pitch Window": {"display": w / 1000}}] for w in (10, 30, 200, 350)]
     + [["fine+50", {"Pitch Fine": {"display": 50}}], ["fine+100", {"Pitch Fine": {"display": 100}}],
        ["fine-100", {"Pitch Fine": {"display": -100}}], ["dw-50", {"Dry/Wet": {"display": 50}}]]},

    {"name": "shifter-lfo", "plan": "8", "probe": "gap2", "read": ["modulation"], "priority": 2,
     "why": "LFO depth in st against Amount, the shapes, and the rate, as pitch modulation of the steady tone (and L/R difference)",
     "question": "FM rate and depth (cents) of the 1 kHz tone, free LFO 1 Hz, Phase mode: Amount 1 and 12 st Sine, 12 st Triangle, Saw Up, Rectangle; Amount 3 st at 5 Hz",
     "base": {**BASE, "Lfo Sync": OFF, "Lfo Rate Hz": {"display": 1.0}, "Lfo Spin": OFF,
              "Lfo Waveform": {"item": "Sine"}, "Lfo Amount St": {"display": 1}},
     "cases": [["amt12-sine", {"Lfo Amount St": {"display": 12}}],
               ["amt12-triangle", {"Lfo Amount St": {"display": 12}, "Lfo Waveform": {"item": "Triangle"}}],
               ["amt12-sawup", {"Lfo Amount St": {"display": 12}, "Lfo Waveform": {"item": "Saw Up"}}],
               ["amt12-rect", {"Lfo Amount St": {"display": 12}, "Lfo Waveform": {"item": "Rectangle"}}],
               ["amt3-5Hz", {"Lfo Amount St": {"display": 3}, "Lfo Rate Hz": {"display": 5.0}}]]},

    {"name": "shifter-envelope", "plan": "9", "probe": "gap2", "read": ["dynamics", "steady (output frequency over time)"], "priority": 3,
     "why": "sign and depth of the envelope follower's shift, and its attack and release",
     "question": "frequency of the three tone bursts (-30, -6, -30 dBFS) with the follower on, Amount +12, -12, +3 st; +12 st with Attack 30 ms and Release 400 ms",
     "base": {**BASE, "Env On": ON, "Env Amount St": {"display": 0}},
     "cases": [["env+12", {"Env Amount St": {"display": 12}}], ["env-12", {"Env Amount St": {"display": -12}}],
               ["env+3", {"Env Amount St": {"display": 3}}],
               ["env+12-slow", {"Env Amount St": {"display": 12}, "Env Attack": {"display": 0.03},
                                "Env Release": {"display": 0.4}}]]},
]
