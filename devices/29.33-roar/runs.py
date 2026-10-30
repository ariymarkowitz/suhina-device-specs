# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Roar behaviour runs for tools/harness/measure.py (see its docstring for the format).
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

    # ---- third set: the routing mode is no API parameter, but the set stores it
    # (Input_RoutingMode, 0 = Single .. 6 = Delay in the Max wrapper's order), so it is written
    # as a stored element
    {"name": "roar-single-routing", "plan": "2, 5", "probe": "gap2", "read": ["static", "response"], "priority": 1,
     "why": "whether a stored Input_RoutingMode reaches the audio: Single (0) should put the 1 kHz staircase through stage 1's shaper",
     "question": "1 kHz staircase and sweep with Shaper 1 Soft Sine at Amt 100 %, routing stored as 0 (Single) and as 3 (Multi Band, the loaded one)",
     "base": {"Shaper 1 Amt": {"display": 100}},
     "cases": [["single", {"@Input_RoutingMode": 0}], ["multiband", {"@Input_RoutingMode": 3}]]},

    # roar-single-routing (pilot) showed that a stored Input_RoutingMode reaches the audio:
    # Single (0) put the staircase through stage 1's shaper. So the shaper, filter and routing
    # runs are repeated in Single and the other modes (0 Single, 1 Serial, 2 Parallel, 3 Multi
    # Band, 4 Mid Side, 5 Feedback, 6 Delay: the Max wrapper's order, to be confirmed by the
    # renders). The modulation matrix cells are stored elements too
    # (ModulationMatrix_<target>_<source>, 0 in the loaded device; their scale is [measure]).
    {"name": "roar-single-shapers", "plan": "2", "probe": "ext", "read": ["ext: ramp, stair100, tone3k, silence (DC)"], "priority": 1,
     "why": "every shaper's curve in Single routing, on the 1 kHz ramp and the 100 Hz staircase; Amount and Bias on Soft Sine",
     "question": "the ramp, 100 Hz staircase and 3 kHz sine through stage 1 (Drive +12 dB, Amt 50 %) for each of the 12 types; Soft Sine at Amt 25 and 100 % and Bias -50 and +50 %",
     "base": dict(SHAPER1, **{"@Input_RoutingMode": 0}),
     "cases": types(["Soft Sine", "Digital Clip", "Bit Crusher", "Diode Clipper", "Tube Preamp", "Half Wave Rectifier",
                     "Full Wave Rectifier", "Polynomial", "Fractal", "Tri Fold", "Noise Injection", "Shards"]) +
              [[f"softsine-amt{a}", {"Shaper 1 Amt": {"display": a}}] for a in (25, 100)] +
              [[f"softsine-bias{b:+d}", {"Shaper 1 Bias": {"display": b / 100}}] for b in (-50, 50)]},

    {"name": "roar-single-filters", "plan": "4", "probe": "gap2", "read": ["response", "impulse"], "priority": 1,
     "why": "the filters in Single routing: each type at 1 kHz, resonance on the low-pass, the Morph cycle, Comb and Resampling against Frequency",
     "question": "sweep response and impulse through stage 1's filter alone at 1 kHz: each type at Res 0.5; LP at Res 0 and 1.0; Morph 0, 0.25, 0.75; Comb and Resampling at 200 Hz; Peak at +12 dB",
     "base": dict(FILTER1, **{"@Input_RoutingMode": 0, "Flt 1 Res": {"display": 0.5}}),
     "cases": [[f"type-{t.lower()}", {"Flt 1 Type": {"item": t}}] for t in ("LP", "BP", "HP", "Notch", "Peak", "Comb", "Resampling", "Dispersion")] +
              [[f"lp-res{r}", {"Flt 1 Type": {"item": "LP"}, "Flt 1 Res": {"display": r}}] for r in (0, 1)] +
              [[f"morph-{m}", {"Flt 1 Type": {"item": "Morph"}, "Flt 1 Morph": {"display": m}}] for m in (0, 0.25, 0.75)] +
              [[f"{t.lower()}-200", {"Flt 1 Type": {"item": t}, "Flt 1 Freq": {"display": 200}}] for t in ("Comb", "Resampling")] +
              [["peak+12", {"Flt 1 Type": {"item": "Peak"}, "Flt 1 Peak": {"display": 12}}]]},

    {"name": "roar-routings", "plan": "5", "probe": "gap2", "read": ["static", "impulse", "stereo", "response"], "priority": 1,
     "why": "the other routing modes: Serial and Parallel with two different shapers and Blend, Mid Side with one-sided input, Feedback and Delay's repeats",
     "question": "stage 1 Digital Clip and stage 2 Soft Sine (Drive +12 dB, Amt 50 %): Serial and Parallel at Blend 0, 50, 100; Mid Side; Feedback and Delay with Feedback 50 % (impulse repeats)",
     "base": dict(SHAPER1, **{"Shaper 1 Type": {"item": "Digital Clip"}, "Shaper 2 On": ON, "Shaper 2 Type": {"item": "Soft Sine"},
                              "Shaper 2 Amt": {"display": 50}}),
     "cases": [[f"{n}-blend{b}", {"@Input_RoutingMode": m, "Blend": {"display": b}}] for n, m in (("serial", 1), ("parallel", 2))
               for b in (0, 50, 100)] +
              [["midside", {"@Input_RoutingMode": 4}],
               ["feedback-fb50", {"@Input_RoutingMode": 5, "Feedback": {"display": 50}}],
               ["delay-fb50", {"@Input_RoutingMode": 6, "Feedback": {"display": 50}}]]},

    {"name": "roar-level-output-hq", "plan": "3, 11", "probe": "ext", "read": ["ext: ramp, tone10k, tone15k peaks", "impulse"], "priority": 2,
     "why": "Shaper Level and Output at their ends with the shaper off, and the stored HiQuality switch against aliasing at high Amount",
     "question": "level of the ramp in Single with shaper 1 bypassed in effect (Amt 0): Shaper 1 Level -24 and +24 dB, Output -48 and +12 dB; the 10 and 15 kHz sines through Digital Clip at Amt 100 %, HiQuality off and on",
     "base": dict(SHAPER1, **{"@Input_RoutingMode": 0}),
     "cases": [[f"level{l:+d}", {"Shaper 1 Amt": {"display": 0}, "Shaper 1 Level": {"display": l}}] for l in (-24, 24)] +
              [[f"output{o:+d}", {"Shaper 1 Amt": {"display": 0}, "Output": {"display": o}}] for o in (-48, 12)] +
              [[f"clip-hq-{'on' if q else 'off'}", {"Shaper 1 Type": {"item": "Digital Clip"}, "Shaper 1 Amt": {"display": 100},
                                                    "@HiQuality": q}] for q in (False, True)]},

    {"name": "roar-modulation", "plan": "9, 10", "probe": "gap2", "read": ["envelope of the steady tone"], "priority": 2,
     "why": "the LFOs, envelope and noise read through the Output gain (matrix cell stored), and the matrix cell's scale",
     "question": "the steady tone in Single, shaper off, LFO 1 free at 1 Hz with ModulationMatrix_Output_Lfo1 stored 1, 50, 100 and -100 (the cell holds whole numbers; its scale is unknown); LFO 1 Square, Ramp Up, Morph +50 %, Smooth 50 %; LFO 2 cell; Noise cell (Simplex, S&H); Env cell on the bursts",
     "base": dict(PASS, **{"@Input_RoutingMode": 0, "Output": {"display": -12}, "LFO 1 Rate Mode": {"item": "Free"},
                           "LFO 1 Rate": {"display": 1}, "LFO 1 Wave": {"item": "Sine"}, "LFO 1 Morph": {"display": 0},
                           "LFO 1 Smooth": {"display": 0}, "@ModulationMatrix_Output_Lfo1": 1}),
     "cases": [[f"lfo1-cell{v:+d}", {"@ModulationMatrix_Output_Lfo1": v}] for v in (50, 100, -100)] +
              [[f"lfo1-{w.lower().replace(' ', '-')}", {"LFO 1 Wave": {"item": w}}] for w in ("Triangle", "Square", "Ramp Up")] +
              [["lfo1-morph+50", {"LFO 1 Morph": {"display": 50}}], ["lfo1-smooth-50", {"LFO 1 Smooth": {"display": 50}}],
               ["noise-simplex", {"@ModulationMatrix_Output_Lfo1": 0, "@ModulationMatrix_Output_Noise": 1,
                                  "Noise Rate Mode": {"item": "Free"}, "Noise Rate": {"display": 1}}],
               ["noise-snh", {"@ModulationMatrix_Output_Lfo1": 0, "@ModulationMatrix_Output_Noise": 1, "Noise Type": {"item": "Sample & Hold"},
                              "Noise Rate Mode": {"item": "Free"}, "Noise Rate": {"display": 4}}],
               ["env", {"@ModulationMatrix_Output_Lfo1": 0, "@ModulationMatrix_Output_Env": 1}]]},
]


def _base(name):
    return next(r for r in RUNS if r["name"] == name)["base"]


def _case(run, case):
    return next(c for r in RUNS if r["name"] == run for c in r["cases"] if c[0] == case)[1]


# ---- fifth set: the matrix cells other than Output (the cell is the swing of the target in units of
# its whole range, read off an LFO 1 square wave at 1 Hz so each half cycle is one extreme)
_MATRIX = dict(_base("roar-modulation"), **{
    "Output": {"display": 0}, "Drive": {"display": 6}, "Tone Amt": {"display": 50}, "Tone Freq": {"display": 1000},
    "Shaper 1 On": 1, "Shaper 1 Type": {"item": "Soft Sine"}, "Shaper 1 Amt": {"display": 50},
    "Flt 1 On": 1, "Flt 1 Type": {"item": "LP"}, "Flt 1 Freq": {"display": 4000}, "Flt 1 Res": {"display": 0.5},
    "LFO 1 Wave": {"item": "Square"}, "@ModulationMatrix_Output_Lfo1": 0})


def _cell(target, source="Lfo1", value=1, **extra):
    return {f"@ModulationMatrix_{target}_{source}": value, **extra}


RUNS += [
    {"name": "roar-matrix-targets", "plan": "10", "probe": "gap2", "read": ["raw render of the steady tone and the noise (per half cycle)"], "priority": 2,
     "why": "only the Output cell was read; the same cell at 1 for the other targets gives each target's range, direction and curve, and three sources and the Global Mod Amt are checked on Input and Output",
     "question": "gain, distortion and spectrum of the steady tone and the noise in each half cycle of an LFO 1 square wave at 1 Hz with one matrix cell stored as 1: Input, Tone Amount, Tone Frequency, Blend, Dry/Wet, Stage 1 Amount, Bias, Trim, Frequency, Resonance, Morph (type Morph), PeakGain (type Peak), Feedback Amount; LFO 2, Noise and Env as sources; the Output cell at Global Mod Amt 50 and 200 %; LFO 2 into LFO 1's Rate",
     "base": _MATRIX,
     "cases": [[f"{t.lower()}", _cell(t)] for t in ("Input", "ToneAmount", "ToneFrequency", "Blend", "DryWet", "Stage1Amount",
                                                   "Stage1Bias", "Stage1Trim", "Stage1Frequency", "Stage1Resonance", "FeedbackAmount")] +
              [["stage1morph", _cell("Stage1Morph", **{"Flt 1 Type": {"item": "Morph"}})],
               ["stage1peakgain", _cell("Stage1PeakGain", **{"Flt 1 Type": {"item": "Peak"}})],
               ["lfo2-input", _cell("Input", "Lfo2", **{"LFO 2 Wave": {"item": "Square"}, "LFO 2 Rate Mode": {"item": "Free"}, "LFO 2 Rate": {"display": 1}})],
               ["noise-input", _cell("Input", "Noise", **{"Noise Type": {"item": "Sample & Hold"}, "Noise Rate Mode": {"item": "Free"}, "Noise Rate": {"display": 4}})],
               ["env-stage1amount", _cell("Stage1Amount", "Env")],
               ["output-ref", _cell("Output")],
               ["output-global50", _cell("Output", **{"Global Mod Amt": {"display": 50}})],
               ["output-global200", _cell("Output", **{"Global Mod Amt": {"display": 200}})],
               ["lfo2-lfo1rate", _cell("Output", **{"@ModulationMatrix_Lfo1Rate_Lfo2": 1, "LFO 2 Wave": {"item": "Square"},
                                                    "LFO 2 Rate Mode": {"item": "Free"}, "LFO 2 Rate": {"display": 0.25}})]]},
]
