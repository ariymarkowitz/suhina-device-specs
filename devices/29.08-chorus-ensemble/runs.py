# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Chorus-Ensemble behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.08-chorus-ensemble.md > Measurement plan.

The impulse (one sample at time 0) reads the delay-line taps: with Amount 0 the taps sit at the
base delays; with the LFO on, the tap moves with the LFO phase at the instant of the impulse.
The steady 1 kHz tone (8 s) shows the modulation as FM (rate, depth in cents) and AM, and the
L/R envelope correlation shows the channels' phase relation. All runs are wet only (Dry/Wet
100 %) unless they are about the mix.

Not taken: LFO phase of the individual taps in Chorus and Ensemble (step 4: the FM trace of a
tone sums the taps, so only the combined modulation is seen; the impulse shows one instant),
loading a pre-12.4 set (step 11, a file test, not an audio one), feedback runaway beyond a
99 % top and Warmth inside the loop (one render per case at one setting), and the mode-switch
transient (needs a parameter change during the render)."""

DEVICE = "Chorus-Ensemble"

# Chorus, two taps at 20 ms, no modulation, no feedback, wet only, flat output.
BASE = {"Mode": {"item": "Chorus"}, "Shape": {"display": 0}, "Rate": {"display": 1}, "Amount": {"display": 0},
        "Feedback": {"display": 0}, "FB Invert": {"item": "Off"}, "Offset": {"display": 0},
        "Delay Time": {"item": "20 ms"}, "Delay Taps": {"item": "2"}, "HP On": {"item": "Off"},
        "Width": {"display": 100}, "Warmth": {"display": 0}, "Output": {"display": 0},
        "Dry/Wet": {"display": 100}}

# The same with the LFO running at full depth, 1 Hz, for the steady-tone reads.
MOD = dict(BASE, **{"Amount": {"display": 100}})

RUNS = [
    {"name": "chorus-base-delay", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "the base delay of every tap: each fixed Delay Time, Auto, one vs two taps, and the Ensemble and Vibrato delays (Amount 0)",
     "question": "impulse taps (time, level, L/R) for Delay Time Auto, 7, 10, 35, 50 ms (the default case is 20 ms), 1 tap, Ensemble and Vibrato",
     "base": BASE,
     "cases": [["auto", {"Delay Time": {"item": "Auto"}}]] +
              [[f"t{t}", {"Delay Time": {"item": f"{t} ms"}}] for t in (7, 10, 35, 50)] +
              [["taps-1", {"Delay Taps": {"item": "1"}}],
               ["ensemble", {"Mode": {"item": "Ensemble"}}],
               ["vibrato", {"Mode": {"item": "Vibrato"}}]]},

    {"name": "chorus-depth-rate", "plan": "3", "probe": "gap2", "read": ["modulation", "stereo"], "priority": 1,
     "why": "modulation depth in cents against Amount and Rate, and the LFO rate actually produced (FM depth and rate of the steady tone)",
     "question": "FM depth and rate of the tone through Chorus (20 ms, 2 taps) for Amount 25, 50, 100 % at 1 Hz and Rate 0.5, 5 Hz at 100 %",
     "base": MOD,
     "cases": [[f"amount-{a}", {"Amount": {"display": a}}] for a in (25, 50)] +
              [[f"rate-{r}", {"Rate": {"display": r}}] for r in (0.5, 5)]},

    {"name": "chorus-auto-amount", "plan": "2", "probe": "gap2", "read": ["impulse", "modulation"],
     "priority": 1,
     "why": "how Auto Delay Time scales with Amount (taps at Amount 25, 50, 100 %; Amount 0 is in chorus-base-delay)",
     "question": "impulse taps and FM depth for Delay Time Auto at Amount 25, 50, 100 %, 2 taps",
     "base": dict(BASE, **{"Delay Time": {"item": "Auto"}}),
     "cases": [[f"auto-amount-{a}", {"Amount": {"display": a}}] for a in (25, 50, 100)]},

    {"name": "chorus-vibrato-shape", "plan": "4", "probe": "gap2", "read": ["modulation", "stereo"],
     "priority": 2,
     "why": "Vibrato's pitch curve (sine to triangle Shape) and the L/R phase from Offset (FM trace per channel)",
     "question": "FM depth, rate and L/R correlation of the tone in Vibrato at 2 Hz for Shape 0, 50, 100 % and Offset 90, 180",
     "base": dict(MOD, **{"Mode": {"item": "Vibrato"}, "Rate": {"display": 2}}),
     "cases": [["shape-50", {"Shape": {"display": 50}}], ["shape-100", {"Shape": {"display": 100}}],
               ["offset-90", {"Offset": {"display": 90}}], ["offset-180", {"Offset": {"display": 180}}]]},

    {"name": "chorus-width", "plan": "6", "probe": "gap2", "read": ["stereo", "modulation"], "priority": 2,
     "why": "Width's mid/side law on the wet signal (L/R levels and correlation for Width 0, 100, 200 % in Chorus and Ensemble)",
     "question": "2x2 level matrix and L/R envelope correlation for Width 0 and 200 % in Chorus and Ensemble at full Amount",
     "base": MOD,
     "cases": [["chorus-w0", {"Width": {"display": 0}}], ["chorus-w200", {"Width": {"display": 200}}],
               ["ensemble-w100", {"Mode": {"item": "Ensemble"}}],
               ["ensemble-w0", {"Mode": {"item": "Ensemble"}, "Width": {"display": 0}}],
               ["ensemble-w200", {"Mode": {"item": "Ensemble"}, "Width": {"display": 200}}]]},

    {"name": "chorus-feedback", "plan": "7", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "feedback repeats: spacing, decay per repeat against Feedback and the effect of Invert, up to 99 %",
     "question": "impulse taps (up to 16) for Feedback 50, 90, 99 % and 90, 99 % inverted, 1 tap at 20 ms, Amount 0",
     "base": dict(BASE, **{"Delay Taps": {"item": "1"}}),
     "cases": [["fb-50", {"Feedback": {"display": 50}}], ["fb-90", {"Feedback": {"display": 90}}],
               ["fb-99", {"Feedback": {"display": 99}}],
               ["fb-90-invert", {"Feedback": {"display": 90}, "FB Invert": {"item": "On"}}],
               ["fb-99-invert", {"Feedback": {"display": 99}, "FB Invert": {"item": "On"}}]]},

    {"name": "chorus-highpass-warmth", "plan": "5, 8", "probe": "gap2", "read": ["response", "static"],
     "priority": 2,
     "why": "the High-Pass filter on the wet path (corner, slope) and Warmth's roll-off and distortion (sweep, THD)",
     "question": "sweep response (Amount 0, so the wet path is static) for HP 50, 200, 1000 Hz and Warmth 50, 100 %; staircase THD for Warmth",
     "base": BASE,
     "cases": [["hp-50", {"HP On": {"item": "On"}}],
               ["hp-200", {"HP On": {"item": "On"}, "HP Freq": {"display": 200}}],
               ["hp-1000", {"HP On": {"item": "On"}, "HP Freq": {"display": 1000}}],
               ["warmth-50", {"Warmth": {"display": 50}}], ["warmth-100", {"Warmth": {"display": 100}}]]},

    {"name": "chorus-mix-output", "plan": "9, 10", "probe": "gap2", "read": ["static", "impulse", "response"],
     "priority": 3,
     "why": "Dry/Wet law, Output's dB law, and whether the dry path is delayed to match (impulse taps at 25 % and 50 %)",
     "question": "level, impulse taps and sweep for Dry/Wet 0, 25, 50 %, Output -12 and +6 dB at Dry/Wet 100",
     "base": BASE,
     "cases": [[f"wet-{w}", {"Dry/Wet": {"display": w}}] for w in (0, 25, 50)] +
              [["out-m12", {"Output": {"display": -12}}], ["out-p6", {"Output": {"display": 6}}]]},

    # ---- third set. The extended probe's impulse train (one impulse every
    # 100 ms for 2 s) gives twenty snapshots of the taps' delays, so each tap's LFO can be followed.
    {"name": "chorus-tap-phases", "plan": "4", "probe": "ext", "read": ["ext: impulsetrain (taps per impulse)"], "priority": 1,
     "why": "the LFO phase of each tap in Chorus and Ensemble (and whether one and two taps differ when modulated)",
     "question": "tap delays of each impulse of the train, Amount 100 %, Rate 1 Hz, Feedback 0: Chorus with 2 taps and 1 tap, Ensemble, Vibrato",
     "base": MOD,
     "cases": [["chorus-2taps", {}], ["chorus-1tap", {"Delay Taps": {"item": "1"}}],
               ["ensemble", {"Mode": {"item": "Ensemble"}}], ["vibrato", {"Mode": {"item": "Vibrato"}}]]},

    {"name": "chorus-mode-switch", "plan": "4", "probe": "gap2", "read": ["raw render around the switch"], "priority": 3,
     "why": "what happens at a mode change while playing (crossfade, click, reset of the LFO)",
     "question": "the steady tone with Mode switching from Chorus to Ensemble at beat 46 (23 s) and to Vibrato at beat 52 (26 s), Amount 100 %",
     "base": MOD,
     "cases": [["switch", {"Mode": {"auto": [[0, {"item": "Chorus"}], [46, {"item": "Ensemble"}], [52, {"item": "Vibrato"}]]}}]]},
]
