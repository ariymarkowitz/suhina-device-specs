# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reverb behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.32-reverb.md › Measurement plan.

The Reverb already has five runs (README.md in this folder: structure, decay, filters, texture, size)
and most of the plan is done (note › Measured). These runs only take up what those left open and
what one probe render can answer: the Lo Cut's law, the network filters at other frequencies,
Freeze/Flat/Cut set statically from the first sample (plan 9, without automation), Smooth Slow
(plan 10, as far as an export shows it), more Spin pairs, and Diffusion/Scale at a second Size.
The base states are those of make_cases.py, so the setup is the same.

Left out (cannot be measured this way): Smooth's glide times and toggling Freeze during the render
(automation); the decay of the 60 s setting past 60 s (the longest probe has a 30 s gap); CPU cost of
Density; the Predelay's 0.06 to 0.09 ms offset (below what an impulse at 44.1 kHz resolves usefully).
"""

DEVICE = "Reverb"

ON, OFF = 1, 0
# Wet only and time-invariant: what the earlier runs start from.
STATIC = {"Dry/Wet": {"display": 100}, "Chorus On": OFF, "ER Spin On": OFF}
ER_ONLY = {"Diffuse Level": {"norm": 0.0}}
TAIL_ONLY = {"Reflect Level": {"norm": 0.0}}
SHORT = {"Decay Time": {"norm": 0.0}}  # 200 ms
NET = {"Decay Time": {"norm": 0.5}, **TAIL_ONLY, "Diff. Hi On": OFF, "Diff. Lo On": OFF}  # 3.46 s, filters off

LOCUT = {**STATIC, **SHORT, "In Lo Cut On": ON, "In Hi Cut On": OFF, "Input Freq": {"display": 1000},
         "Input Width": {"display": 5.85}}


def shelf(typ, freq, gain=0.4):
    return {"Diff. Hi On": ON, "Diff. Hi Type": {"item": typ}, "Diff. Hi Freq": {"display": freq},
            "HiShelf Gain": {"display": gain}}


SMALL_SMOOTH_NONE = {**STATIC, "Size Smoothing": {"item": "None"}}

RUNS = [
    {"name": "reverb-locut-law", "plan": "3", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "the Lo Cut's law, which the note calls not understood: corner against Input Freq and Input Width",
     "question": "sweep response of the Lo Cut alone (Hi Cut off, short tail) against Input Width at 1 kHz and Input Freq at Width 5.85",
     "base": LOCUT,
     "cases": [[f"lo-1k-w{w:g}", {"Input Width": {"display": w}}] for w in (0.5, 2, 4.75, 9)]
     + [["lo-300Hz", {"Input Freq": {"display": 300}}], ["lo-2k", {"Input Freq": {"display": 2000}}]]},

    {"name": "reverb-network-freq", "plan": "6", "probe": "gap10", "read": ["impulse"], "priority": 2,
     "why": "the High shelf/Lowpass and Low shelf at other frequencies: shelf midpoint and order, Lowpass corner",
     "question": "decay per octave band (filtered .ir.wav) with the High filter at 250 Hz, 4 kHz, 12 kHz, Lowpass at 250 Hz and 4 kHz, Low shelf at 200 Hz and 2 kHz, gain 0.4",
     "base": {**STATIC, **NET},
     "cases": [["hi-shelf-250", shelf("Shelf", 250)], ["hi-shelf-4k", shelf("Shelf", 4000)],
               ["hi-shelf-12k", shelf("Shelf", 12000)],
               ["hi-lowpass-250", shelf("Lowpass", 250)], ["hi-lowpass-4k", shelf("Lowpass", 4000)],
               ["lo-shelf-200", {"Diff. Lo On": ON, "Diff. Lo Freq": {"display": 200}, "LowShelf Gain": {"display": 0.4}}],
               ["lo-shelf-2k", {"Diff. Lo On": ON, "Diff. Lo Freq": {"display": 2000}, "LowShelf Gain": {"display": 0.4}}]]},

    {"name": "reverb-freeze-static", "plan": "9", "probe": "gap10", "read": ["impulse"], "priority": 2,
     "why": "what Freeze with Cut and Flat does when on from the first sample: does the impulse enter, does the tail sustain, do the shelves drain it",
     "question": "energy of the response to the impulse over 10 s with Freeze on at Cut/Flat on/off, both network filters on, against Freeze off",
     "base": {**STATIC, "Decay Time": {"norm": 0.5}, "Diff. Hi On": ON, "Diff. Lo On": ON, "Freeze On": ON},
     "cases": [["cut-noflat", {"Flat On": OFF}],
               ["nocut-flat", {"Cut On": OFF}],
               ["nocut-noflat", {"Cut On": OFF, "Flat On": OFF}],
               ["freeze-off", {"Freeze On": OFF}]]},

    {"name": "reverb-smooth-slow", "plan": "10", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "whether Size Smoothing Slow also ignores a Size set through the set (only Fast was tested); Size 1.53 and 10.54",
     "question": "early-reflection taps at Size 10.54 and 1.53 with Smooth None, Slow and Fast (the preset)",
     "base": {**STATIC, **ER_ONLY, **SHORT, "Room Size": {"display": 10.54}},
     "cases": [["none-10.54", {"Size Smoothing": {"item": "None"}}],
               ["slow-10.54", {"Size Smoothing": {"item": "Slow"}}],
               ["none-1.53", {"Size Smoothing": {"item": "None"}, "Room Size": {"display": 1.53}}],
               ["slow-1.53", {"Size Smoothing": {"item": "Slow"}, "Room Size": {"display": 1.53}}]]},

    {"name": "reverb-spin-grid", "plan": "4", "probe": "gap2", "read": ["modulation"], "priority": 3,
     "why": "Spin depth in ms against Rate and Amount at more points than the four measured (linearity in each, the 20 % uncertainty)",
     "question": "FM of the 1 kHz tone through the early reflections alone for Spin Amount x Rate pairs",
     "base": {**STATIC, **ER_ONLY, **SHORT, "ER Spin On": ON},
     "cases": [[f"spin-amt{a:g}-{r:g}Hz", {"ER Spin Amount": {"display": a}, "ER Spin Rate": {"display": r}}]
               for a, r in ((17.5, 0.07), (17.5, 0.6), (5, 1.3), (35, 0.15), (55, 1.3))]},

    {"name": "reverb-diffusion-size10", "plan": "7", "probe": "gap2", "read": ["impulse"], "priority": 3,
     "why": "Diffusion and Scale at a larger Size (Smooth None): echo density build-up and comb colouring, to separate them from Size",
     "question": "echo density over 0 to 0.5 s and the spectrum of the response for Diffusion 0.1 and 96 %, Scale 5 and 100 % at Size 10.54",
     "base": {**SMALL_SMOOTH_NONE, "Room Size": {"display": 10.54}},
     "cases": [["diffusion-0.1", {"Diffusion": {"display": 0.1}}], ["diffusion-96", {"Diffusion": {"display": 96}}],
               ["scale-5", {"Scale": {"display": 5}}], ["scale-100", {"Scale": {"display": 100}}]]},

    # ---- third set (measurements/third/): Freeze and Size changed by automation lanes during the
    # render (make_als.py {"auto": ...}). On the gap10 probe the impulse is at 0.5 s (beat 1) and
    # the sweep starts at 10.5 s (beat 21).
    {"name": "reverb-freeze-toggle", "plan": "9", "probe": "gap10", "read": ["raw render (level over time)", "response"], "priority": 1,
     "why": "Freeze pressed after the impulse and released later: the loop's level over time, whether the sweep enters while frozen, Flat and Cut",
     "question": "Freeze on at beat 2 (1 s) and off at beat 40 (20 s), Decay 3.46 s: Flat off and on with Cut off, and Cut on",
     "base": dict(STATIC, **{"Decay Time": {"norm": 0.5},
                             "Freeze On": {"auto": [[0, OFF], [2, ON], [40, OFF]]}}),
     "cases": [["flat-off", {"Flat On": OFF, "Cut On": OFF}], ["flat-on", {"Flat On": ON, "Cut On": OFF}],
               ["cut-on", {"Flat On": OFF, "Cut On": ON}]]},

    {"name": "reverb-smooth-glide", "plan": "10", "probe": "gap2", "read": ["impulse (tap times against time)"], "priority": 1,
     "why": "the Size glide under Smooth None, Slow and Fast: Size jumps from 10 to 100 just before the impulse, so the early taps show where the glide is",
     "question": "early reflection taps of the impulse with Room Size jumping from 10 to 100 at beat 0.9 (45 ms before the impulse), each Size Smoothing",
     "base": dict(STATIC, **SHORT, **{"Room Size": {"auto": [[0, {"display": 10}], [0.9, {"display": 10}], [0.9, {"display": 100}]]}}),
     "cases": [[s.lower(), {"Size Smoothing": {"item": s}}] for s in ("None", "Slow", "Fast")]},
]
