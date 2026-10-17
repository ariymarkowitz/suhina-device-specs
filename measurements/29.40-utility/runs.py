# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Utility behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.40-utility.md › Measurement plan.

The probe is stereo with identical channels in the impulse, sweep, staircase and steady tone, one
channel at a time in `left` and `right`, and independent noise in L and R. So the stereo matrix of
the `left` and `right` segments (a 1 kHz tone in one channel is half mid, half side) gives the Width,
Balance and Mono laws directly, and the noise gives the crossover of Bass Mono.

Left out (cannot be measured this way): the Mid/Side knob (no API parameter; Width is the only way
to set the side level here), Bass Mono Audition, smoothing and click behaviour on Gain/Mute changes
(automation), the DC step response (no DC in the probe). Stage order (plan 2) is covered only for
the pairs in utility-channels-order.
"""

DEVICE = "Utility"

ON, OFF = 1, 0
STEREO = {"Channel Mode": {"item": "Stereo"}}

RUNS = [
    {"name": "utility-width", "plan": "3", "probe": "gap2", "read": ["stereo", "noise"], "priority": 1,
     "why": "the Width law: side gain against Width 0 to 400 %, normalisation of mid and side, and the behaviour above 100 %",
     "question": "2x2 level matrix (left-only and right-only 1 kHz) and noise correlation for Width 0, 50, 150, 200, 400 %",
     "base": STEREO,
     "cases": [[f"w{w}", {"Stereo Width": {"display": w}}] for w in (0, 50, 150, 200, 400)]},

    {"name": "utility-gain", "plan": "7", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the Gain taper: typed dB against measured dB from -60 dB to +35 dB, the curve below -18 dB and -inf",
     "question": "staircase gain for Gain -inf, -60, -30, -12, +12, +35 dB",
     "base": STEREO,
     "cases": [["gain--inf", {"Output": -1}]] + [[f"gain{g:+d}", {"Output": {"display": g}}] for g in (-60, -30, -12, 12, 35)]},

    {"name": "utility-bass-mono", "plan": "6", "probe": "gap2", "read": ["noise", "stereo"], "priority": 1,
     "why": "the Bass Mono crossover: order, -3 dB point and slope at 50, 120 (default), 250 and 500 Hz",
     "question": "per-channel noise response (independent L/R: below the crossover each channel keeps the mid only, 3 dB down) with Bass Mono on",
     "base": {**STEREO, "Bass Mono": ON, "Bass Freq": {"display": 120}},
     "cases": [[f"bm-{f}Hz", {"Bass Freq": {"display": f}}] for f in (50, 250, 500)]},

    {"name": "utility-channels-order", "plan": "2, 5, 11", "probe": "gap2", "read": ["stereo", "impulse (polarity)", "noise"], "priority": 2,
     "why": "Channel Mode and the phase buttons (before or after the mode), the Mono sum law, and the order of Balance, Bass Mono and Mono",
     "question": "2x2 matrix and impulse polarity for Left, Right, Swap, Mono; Right Inv with Mono; Ø R in Left mode and Ø L in Right mode; Balance 50R into Bass Mono 500 Hz",
     "base": STEREO,
     "cases": [["mode-left", {"Channel Mode": {"item": "Left"}}], ["mode-right", {"Channel Mode": {"item": "Right"}}],
               ["mode-swap", {"Channel Mode": {"item": "Swap"}}], ["mono", {"Mono": ON}],
               ["invR-mono", {"Right Inv": ON, "Mono": ON}],
               ["modeL-invR", {"Channel Mode": {"item": "Left"}, "Right Inv": ON}],
               ["modeR-invL", {"Channel Mode": {"item": "Right"}, "Left Inv": ON}],
               ["bal+1-bassmono500", {"Balance": 1, "Bass Mono": ON, "Bass Freq": {"display": 500}}]]},

    {"name": "utility-balance", "plan": "8", "probe": "gap2", "read": ["stereo"], "priority": 2,
     "why": "the Balance pan law (linear or constant power, centre level) from the matrix at 25 and 50 on each side",
     "question": "2x2 matrix (left-only and right-only 1 kHz) for Balance 50L, 25L, 25R, 50R (internal -1, -0.5, 0.5, 1)",
     "base": STEREO,
     "cases": [[f"bal{b:+g}", {"Balance": b}] for b in (-1, -0.5, 0.5, 1)]},

    {"name": "utility-dc", "plan": "9", "probe": "gap2", "read": ["response"], "priority": 3,
     "why": "the DC filter's corner and slope, from the bottom octave of the sweep (20 Hz and up)",
     "question": "sweep response with the DC filter on",
     "base": STEREO,
     "cases": [["dc-on", {"DC Filter": ON}]]},
]
