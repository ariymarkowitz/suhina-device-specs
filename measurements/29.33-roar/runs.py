# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Roar behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.33-roar.md › Measurement plan.

The routing mode is not an API parameter (the dump has none), so every run plays in the mode the
device loads with (stored 3; unknown which). The first run finds out what that mode does with the
three stages; the later ones put their settings in stage 1 and leave stages 2 and 3 as pass-through
(shaper and filter off), and say so in `question`, since in a mode that does not feed stage 1 from the
input (Multi Band, Mid Side) they would show a band or channel only.

Left out (cannot be measured this way): the other six routing modes (not settable); the whole
modulation section, plan 9 and 10 (LFO, envelope follower and noise have no target without the
matrix cells, which are not API parameters); the sidechain and MIDI feedback note (no external
input, no MIDI); Hi-Quality (a plain value, not settable); parameter changes during the render.
Latency (plan 11) is read from the impulse of any case. Dry/Wet is a plain crossfade check inside
roar-compressor-output.
"""

DEVICE = "Roar"

ON, OFF = 1, 0
# Pass-through everywhere: no tone tilt, no compressor, no shaper, no filter, no feedback, wet only.
PASS = {"Dry/Wet": {"display": 100}, "Tone Amt": {"display": 0}, "Comp Amt": {"display": 0},
        "Feedback": {"display": 0}, "Fb Gate On": OFF,
        **{f"Shaper {n} On": OFF for n in (1, 2, 3)}, **{f"Flt {n} On": OFF for n in (1, 2, 3)}}
# Stage 1 shaper alone, driven 12 dB into the curve so the staircase (-60 to 0 dBFS) spans linear and saturated.
SHAPER1 = {**PASS, "Shaper 1 On": ON, "Drive": {"display": 12}, "Shaper 1 Amt": {"display": 50}}
FILTER1 = {**PASS, "Flt 1 On": ON, "Flt 1 Freq": {"display": 1000}}


def types(names):
    return [[f"type-{n.lower().replace(' ', '-')}", {"Shaper 1 Type": {"item": n}}] for n in names]


RUNS = [
    {"name": "roar-routing-default", "plan": "5", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "which routing the loaded device is in (stored 3) and how off stages and Blend behave, so the other Roar runs can be read",
     "question": "sweep response with stage 1 LP 500 Hz, stage 2 HP 2 kHz, stage 3 notch 1 kHz (shapers off): all stages, each alone, Blend at both ends",
     "base": {**PASS, "Flt 1 On": ON, "Flt 1 Type": {"item": "LP"}, "Flt 1 Freq": {"display": 500},
              "Flt 2 On": ON, "Flt 2 Type": {"item": "HP"}, "Flt 2 Freq": {"display": 2000},
              "Flt 3 On": ON, "Flt 3 Type": {"item": "Notch"}, "Flt 3 Freq": {"display": 1000}},
     "cases": [["s1-only", {"Stage 2 On": OFF, "Stage 3 On": OFF}],
               ["s2-only", {"Stage 1 On": OFF, "Stage 3 On": OFF}],
               ["s3-only", {"Stage 1 On": OFF, "Stage 2 On": OFF}],
               ["blend-0", {"Blend": {"norm": 0.0}}],
               ["blend-100", {"Blend": {"norm": 1.0}}]]},

    {"name": "roar-shaper-types-a", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "transfer curve and harmonics of the six main saturating shapers (default Soft Sine is the run's default case)",
     "question": "1 kHz staircase through stage 1, Drive +12 dB, Amount 50 %, filter off, for Soft Sine, Digital Clip, Diode Clipper, Tube Preamp, Polynomial, Tri Fold",
     "base": SHAPER1,
     "cases": types(["Digital Clip", "Diode Clipper", "Tube Preamp", "Polynomial", "Tri Fold"])},

    {"name": "roar-shaper-amount-bias", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "what Amount and Bias do to the curve (drive into the curve; even harmonics, silence at extreme bias)",
     "question": "1 kHz staircase through Soft Sine and Digital Clip at Amount 10, 25, 100 % and Soft Sine at Bias +-0.5",
     "base": SHAPER1,
     "cases": [["soft-a10", {"Shaper 1 Amt": {"display": 10}}], ["soft-a25", {"Shaper 1 Amt": {"display": 25}}],
               ["soft-a100", {"Shaper 1 Amt": {"display": 100}}],
               ["clip-a25", {"Shaper 1 Type": {"item": "Digital Clip"}, "Shaper 1 Amt": {"display": 25}}],
               ["clip-a100", {"Shaper 1 Type": {"item": "Digital Clip"}, "Shaper 1 Amt": {"display": 100}}],
               ["soft-bias+0.5", {"Shaper 1 Bias": {"display": 0.5}}],
               ["soft-bias-0.5", {"Shaper 1 Bias": {"display": -0.5}}]]},

    {"name": "roar-tone", "plan": "1", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "the Tone tilt: shelf gains, pivot and slope against Amount and Frequency, and Color Compensation flattening it",
     "question": "sweep response with shapers and filters off for Tone Amount -100, -50, 50, 100 % at 180 Hz, +100 % at 2 kHz, and +100 % with Color Compensation",
     "base": PASS,
     "cases": [[f"tone{a:+d}", {"Tone Amt": {"display": a}}] for a in (-100, -50, 50, 100)]
     + [["tone+100-2k", {"Tone Amt": {"display": 100}, "Tone Freq": {"display": 2000}}],
        ["tone+100-color", {"Tone Amt": {"display": 100}, "Color On": ON}]]},

    {"name": "roar-filter-types", "plan": "4", "probe": "gap2", "read": ["response", "impulse"], "priority": 1,
     "why": "slopes, peak gains and shapes of the nine filter types at 1 kHz (the default case is LP)",
     "question": "sweep and impulse through stage 1's filter alone at 1 kHz, Resonance 0.1: BP, HP, Notch, Peak +12 dB, Morph 0.5, Comb, Resampling, Dispersion",
     "base": FILTER1,
     "cases": [["bp", {"Flt 1 Type": {"item": "BP"}}], ["hp", {"Flt 1 Type": {"item": "HP"}}],
               ["notch", {"Flt 1 Type": {"item": "Notch"}}],
               ["peak+12", {"Flt 1 Type": {"item": "Peak"}, "Flt 1 Peak": {"display": 12}}],
               ["morph-0.5", {"Flt 1 Type": {"item": "Morph"}, "Flt 1 Morph": {"display": 0.5}}],
               ["comb", {"Flt 1 Type": {"item": "Comb"}}],
               ["resampling", {"Flt 1 Type": {"item": "Resampling"}}],
               ["dispersion", {"Flt 1 Type": {"item": "Dispersion"}}]]},

    {"name": "roar-feedback", "plan": "6", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "feedback delay times (Time, Synced, Note), level per repeat, inversion and the gate",
     "question": "repeat times and levels of an impulse with Feedback 50 %, gate off, loop band-pass wide open: Time 5/50/250 ms, Synced 1/8, Note A2, Invert, 25 %, gate on",
     "base": {**PASS, "Feedback": {"display": 50}, "FB Freq": {"display": 1000}, "FB Width": {"display": 9},
              "FB Time Mode": {"item": "Time"}, "FB Time": {"display": 0.1}},
     "cases": [["time-5ms", {"FB Time": {"display": 0.005}}], ["time-50ms", {"FB Time": {"display": 0.05}}],
               ["time-250ms", {"FB Time": {"display": 0.25}}],
               ["synced-1/8", {"FB Time Mode": {"item": "Synced"}, "FB Synced": -3}],
               ["note-A2", {"FB Time Mode": {"item": "Note"}, "FB Note": 45}],
               ["invert", {"FB Invert": ON}], ["fb-25", {"Feedback": {"display": 25}}],
               ["gate-on", {"Fb Gate On": ON}]]},

    {"name": "roar-filter-res", "plan": "4", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "Resonance law (peak height, Q) for LP and BP, and the Morph sweep",
     "question": "sweep response of stage 1's filter at 1 kHz: LP at Resonance 0, 0.5, 1; BP at 0.5, 1; Morph at 0.25, 0.75, 1",
     "base": FILTER1,
     "cases": [["lp-res0", {"Flt 1 Res": {"display": 0.0}}], ["lp-res0.5", {"Flt 1 Res": {"display": 0.5}}],
               ["lp-res1", {"Flt 1 Res": {"display": 1.0}}],
               ["bp-res0.5", {"Flt 1 Type": {"item": "BP"}, "Flt 1 Res": {"display": 0.5}}],
               ["bp-res1", {"Flt 1 Type": {"item": "BP"}, "Flt 1 Res": {"display": 1.0}}]]
     + [[f"morph-{m:g}", {"Flt 1 Type": {"item": "Morph"}, "Flt 1 Morph": {"display": m}}] for m in (0.25, 0.75, 1.0)]},

    {"name": "roar-compressor-output", "plan": "3, 7, 8", "probe": "gap2", "read": ["static", "dynamics"], "priority": 2,
     "why": "the built-in compressor's curve and time constants, Drive/Output gain, the 0 dBFS hard clip and Dry/Wet",
     "question": "staircase and bursts with shapers off for Comp Amount 50 and 100 % (SC high-pass on and off), Drive +24 dB into the output clip, Output +12 dB, Dry/Wet 50 % at Drive +24",
     "base": PASS,
     "cases": [["comp-50", {"Comp Amt": {"display": 50}}], ["comp-100", {"Comp Amt": {"display": 100}}],
               ["comp-100-nohp", {"Comp Amt": {"display": 100}, "Comp Hp On": OFF}],
               ["drive+24", {"Drive": {"display": 24}}], ["out+12", {"Output": {"display": 12}}],
               ["drive+24-dw50", {"Drive": {"display": 24}, "Dry/Wet": {"display": 50}}]]},

    {"name": "roar-shaper-types-b", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "transfer curves and harmonics of the other six shapers (rectifiers, Fractal, Noise Injection, Shards)",
     "question": "1 kHz staircase through stage 1, Drive +12 dB, Amount 50 %, for Bit Crusher, Half and Full Wave Rectifier, Fractal, Noise Injection, Shards",
     "base": SHAPER1,
     "cases": types(["Bit Crusher", "Half Wave Rectifier", "Full Wave Rectifier", "Fractal", "Noise Injection", "Shards"])},
]
