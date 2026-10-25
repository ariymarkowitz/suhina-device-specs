# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Saturator behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.34-saturator.md › Measurement plan.

The transfer curves are read from the staircase (1 kHz sine, -60 to 0 dBFS in 3 dB steps): output
level and harmonics per input level, with Drive raising the staircase into the curve. A slow ramp
(plan 1) is not in the probe, so each curve is sampled at 21 levels instead.

Left out (cannot be measured this way): Hi-Quality on/off and the oversampling factor (plan 7; the
setting is a plain value, not an API parameter; every render here uses the loaded state, on);
the DC step response of the Pre-DC filter (the probe has no DC or step input); latency (plan 7, read from the impulse of any case).
"""

DEVICE = "Saturator"

ON, OFF = 1, 0
# Colour filters out of the way, no post clip, wet only, 18 dB of Drive so the staircase spans -42 to +18 dB
# at the curve (linear at the bottom, saturated at the top).
BASE = {"Color On": OFF, "Post Clip Mode": {"item": "No Clip"}, "Drive": {"display": 18},
        "Output": {"display": 0}, "Dry/Wet": {"display": 100}}
WS = {"Color On": OFF, "Post Clip Mode": {"item": "No Clip"}, "Drive": {"display": 0}, "Output": {"display": 0},
      "Dry/Wet": {"display": 100}, "Type": {"item": "Waveshaper"}, "WS Drive": {"display": 100},
      "WS Curve": {"display": 0}, "WS Depth": {"display": 0}, "WS Linearity": {"display": 50},
      "WS Damp": {"display": 0}, "WS Period": {"display": 0}}

RUNS = [
    {"name": "saturator-curves", "plan": "1", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the seven fixed curves: knee, slope at the origin, clip level, fold positions, harmonics (Analog Clip is the default case)",
     "question": "staircase output and harmonics at Drive +18 dB, Color off, for Soft Sine, Bass Shaper (-50 dB), Medium, Hard, Sinoid Fold, Digital Clip",
     "base": BASE,
     "cases": [[f"type-{n.split()[0].lower()}", {"Type": {"item": n}}] for n in
               ("Soft Sine", "Bass Shaper", "Medium Curve", "Hard Curve", "Sinoid Fold", "Digital Clip")]},

    {"name": "saturator-drive-output-mix", "plan": "1, 4", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "Drive and Output gain laws (display dB against real dB, also below the knee) and the Dry/Wet law",
     "question": "Analog Clip staircase at Drive -12, 0, +12, +30, +36 dB; Output -12 and -36 dB; Dry/Wet 50 % at Drive +18",
     "base": BASE,
     "cases": [[f"drive-{d:+d}", {"Drive": {"display": d}}] for d in (-12, 0, 12, 30, 36)]
     + [["out-12", {"Output": {"display": -12}}], ["out-36", {"Output": {"display": -36}}],
        ["dw-50", {"Dry/Wet": {"display": 50}}]]},

    {"name": "saturator-color", "plan": "5", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "where each Color filter raises or lowers the saturation (type, frequency, width, gain) and that the net linear response stays flat",
     "question": "sweep (-12 dBFS) through Digital Clip at Drive +12 dB with Amt Lo +-100 %, Amt Hi +-100 % at 1 kHz/30 %, Amt Hi +100 % at 200 Hz/100 % and at width 0; linear check with Analog Clip at Drive -24 dB",
     "base": {**BASE, "Color On": ON, "Type": {"item": "Digital Clip"}, "Drive": {"display": 12},
              "Color Amt Low": {"display": 0}, "Color Amt Hi": {"display": 0}},
     "cases": [["lo+100", {"Color Amt Low": {"display": 100}}], ["lo-100", {"Color Amt Low": {"display": -100}}],
               ["hi+100", {"Color Amt Hi": {"display": 100}}], ["hi-100", {"Color Amt Hi": {"display": -100}}],
               ["hi+100-200Hz-w100", {"Color Amt Hi": {"display": 100}, "Color Freq": {"display": 200},
                                      "Color Width": {"display": 100}}],
               ["hi+100-w0", {"Color Amt Hi": {"display": 100}, "Color Width": {"display": 0}}],
               ["linear-check", {"Type": {"item": "Analog Clip"}, "Drive": {"display": -24},
                                 "Color Amt Low": {"display": 100}, "Color Amt Hi": {"display": 100}}]]},

    {"name": "saturator-waveshaper", "plan": "3", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "the Waveshaper's transfer function: Curve, Linear, Damp (dead zone), Depth and Period ripples, Shaper Drive crossfade",
     "question": "staircase at Drive 0 dB through the Waveshaper (all zero except Linear 50 %): Curve 50 and 100 %, Linear 0 and 100 %, Damp 50 %, Depth 50 % alone and with Period 50 %, Shaper Drive 50 %",
     "base": WS,
     "cases": [["curve-50", {"WS Curve": {"display": 50}}], ["curve-100", {"WS Curve": {"display": 100}}],
               ["lin-0", {"WS Linearity": {"display": 0}}], ["lin-100", {"WS Linearity": {"display": 100}}],
               ["damp-50", {"WS Damp": {"display": 50}}], ["depth-50", {"WS Depth": {"display": 50}}],
               ["depth-50-period-50", {"WS Depth": {"display": 50}, "WS Period": {"display": 50}}],
               ["wsdrive-50", {"WS Curve": {"display": 100}, "WS Drive": {"display": 50}}]]},

    {"name": "saturator-bass-shaper", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "the Bass Shaper's knee against Threshold (linear below it, soft above) compared with Analog Clip",
     "question": "staircase at Drive +18 dB for Threshold 0, -12, -25, -40 dB (default -50 dB is the default case)",
     "base": {**BASE, "Type": {"item": "Bass Shaper"}},
     "cases": [[f"thr-{t}", {"Threshold": {"display": -t}}] for t in (0, 12, 25, 40)]},

    {"name": "saturator-postclip", "plan": "6", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "post clip ceiling for Soft and Hard, and whether it sits before or after the Output attenuation",
     "question": "staircase at Drive +24 dB (Analog Clip) for No Clip, Soft Clip and Hard Clip at Output 0 and -6 dB",
     "base": {**BASE, "Drive": {"display": 24}},
     "cases": [["none-out-6", {"Output": {"display": -6}}],
               ["soft-out0", {"Post Clip Mode": {"item": "Soft Clip"}}],
               ["soft-out-6", {"Post Clip Mode": {"item": "Soft Clip"}, "Output": {"display": -6}}],
               ["hard-out0", {"Post Clip Mode": {"item": "Hard Clip"}}],
               ["hard-out-6", {"Post Clip Mode": {"item": "Hard Clip"}, "Output": {"display": -6}}]]},

    {"name": "saturator-predc", "plan": "8", "probe": "gap2", "read": ["response"], "priority": 3,
     "why": "the Pre-DC filter's corner and slope (a high-pass at the input), from the sweep's lowest octave",
     "question": "sweep response at Drive 0 dB (Analog Clip, linear) with Pre-DC off and on, and on at Drive +18 dB",
     "base": {**BASE, "Drive": {"display": 0}},
     "cases": [["predc-on", {"Pre Dc Filter": ON}],
               ["predc-on-drive18", {"Pre Dc Filter": ON, "Drive": {"display": 18}}]]},

    # ---- third set: Hi-Quality is the stored element Oversampling (on in the loaded preset)
    {"name": "saturator-hiquality", "plan": "7", "probe": "ext", "read": ["ext: tone10k, tone15k peaks"], "priority": 1,
     "why": "aliasing with Hi-Quality off and on (stored element Oversampling), Analog Clip at Drive +24 dB",
     "question": "spectral lines of the 10 and 15 kHz sines at Drive +24 dB with Oversampling stored on and off",
     "base": {"Drive": {"display": 24}},
     "cases": [["hq-on", {"@Oversampling": True}], ["hq-off", {"@Oversampling": False}]]},

    # ---- third set (measurements/third/): the extended probe's 1 kHz ramp (-60 to 0 dBFS and
    # back at 10 dB/s) gives each curve in 0.5 dB steps; Hi-Quality is the stored element
    # Oversampling (on in the loaded device; saturator-hiquality, in the pilot, read it at 88.2 kHz)
    {"name": "saturator-curves-ramp", "plan": "1", "probe": "ext", "read": ["ext: ramp, stair100"], "priority": 1,
     "why": "the fixed curves and Bass Shaper on the fine ramp and at 100 Hz, at Drive 0 and +18 dB",
     "question": "gain and harmonics against level on the ramp and the 100 Hz staircase for each fixed Type at Drive 0 and +18 dB, Hi-Quality on",
     "base": BASE,
     "cases": [[f"{t.lower().replace(' ', '-')}-d{d}", {"Type": {"item": t}, "Drive": {"display": d}}]
               for t in ("Analog Clip", "Soft Sine", "Bass Shaper", "Medium Curve", "Hard Curve", "Sinoid Fold", "Digital Clip")
               for d in (0, 18)]},

    {"name": "saturator-hiquality-types", "plan": "7", "probe": "ext", "read": ["ext: tone10k, tone15k peaks"], "priority": 1,
     "why": "aliasing with Hi-Quality off and on, at 44.1 kHz, for the clip, the fold and the Waveshaper",
     "question": "spectral lines of the 10 and 15 kHz sines at Drive +24 dB for Analog Clip, Digital Clip, Sinoid Fold and Waveshaper, Oversampling true and false",
     "base": dict(BASE, **{"Drive": {"display": 24}}),
     "cases": [[f"{t.lower().replace(' ', '-')}-hq-{'on' if q else 'off'}", {"Type": {"item": t}, "@Oversampling": q}]
               for t in ("Analog Clip", "Digital Clip", "Sinoid Fold", "Waveshaper") for q in (True, False)]},

    {"name": "saturator-waveshaper-more", "plan": "3", "probe": "ext", "read": ["ext: ramp, stair100, dcstep"], "priority": 2,
     "why": "the Waveshaper's controls at intermediate values (polynomial terms, the sine's depth and period, Damp's dead zone, Shaper Drive's crossfade)",
     "question": "the ramp, 100 Hz staircase and DC step for Curve 25, 75, 100 %; Depth 25 and 75 % at Period 50 %; Damp 25 and 75 %; Linearity 0 and 100 %; WS Drive 0 and 50 %",
     "base": WS,
     "cases": [[f"curve-{v}", {"WS Curve": {"display": v}}] for v in (25, 75, 100)] +
              [[f"depth-{v}", {"WS Depth": {"display": v}, "WS Period": {"display": 50}}] for v in (25, 75)] +
              [[f"damp-{v}", {"WS Damp": {"display": v}}] for v in (25, 75)] +
              [[f"linearity-{v}", {"WS Linearity": {"display": v}}] for v in (0, 100)] +
              [[f"wsdrive-{v}", {"WS Drive": {"display": v}}] for v in (0, 50)]},

    {"name": "saturator-color-more", "plan": "5", "probe": "gap2", "read": ["response", "static"], "priority": 2,
     "why": "the colour filters' negative amounts, other frequencies and intermediate amounts, read through Digital Clip",
     "question": "sweep and staircase through Digital Clip at Drive +12 dB with Color on: Amt Lo -100 %; Amt Hi -100 %; Amt Hi +50 % at 200 Hz and 5 kHz (Width 30 %)",
     "base": dict(BASE, **{"Type": {"item": "Digital Clip"}, "Drive": {"display": 12}, "Color On": ON,
                           "Color Amt Low": {"display": 0}, "Color Amt Hi": {"display": 0}, "Color Width": {"display": 30}}),
     "cases": [["lo-100", {"Color Amt Low": {"display": -100}}], ["hi-100", {"Color Amt Hi": {"display": -100}}]] +
              [[f"hi50-{f}", {"Color Amt Hi": {"display": 50}, "Color Freq": {"display": f}}] for f in (200, 5000)]},

    {"name": "saturator-predc-step", "plan": "8", "probe": "ext", "read": ["ext: dcstep, lowsines"], "priority": 2,
     "why": "the Pre-DC filter's step response and its effect on 1, 5 and 20 Hz",
     "question": "the DC step and the 1, 5, 20 Hz sines at Drive 0, Pre Dc Filter off and on",
     "base": dict(BASE, **{"Drive": {"display": 0}}),
     "cases": [["predc-off", {"Pre Dc Filter": OFF}], ["predc-on", {"Pre Dc Filter": ON}]]},
]
