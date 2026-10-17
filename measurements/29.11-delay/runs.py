# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Delay behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.11-delay.md > Measurement plan.

The impulse (one sample at time 0, both channels) reads the delay times and the repeats: up to 16
taps with time and level per channel. Left and right are set to different times in most runs so
one render reads both. Tempo is 120 BPM (a sixteenth is 125 ms). Stereo Link is off, with both
channels set explicitly. Repeats must fit the 2 s gap, so times stay at or below 1 s.

Not taken: Freeze (step 9: it needs a press during the render, and a buffer filled with nothing
before it), the transition when the delay time is changed by hand (step 7: no parameter changes;
the Repitch / Fade / Jump modes are read through LFO modulation instead, which drives the same
mechanism), Hi-Quality and Equal-Loudness (context-menu options, not parameters), the Sync
button 16 (2 s, as long as the gap; follows from the formula), Rate modes other than Rate (the
period lists are Auto Pan-Tremolo's and Auto Filter's problem), tempo change while playing."""

DEVICE = "Delay"

# Time mode, left 100 ms and right 200 ms, no feedback, no filter, no LFO, 100 % wet.
BASE = {"Smoothing": {"item": "Repitch"}, "Link": {"item": "Off"}, "Ping Pong": {"item": "Off"},
        "L Sync": {"item": "Off"}, "R Sync": {"item": "Off"},
        "L Time": {"display": 0.1}, "R Time": {"display": 0.2},
        "L Offset": {"display": 0}, "R Offset": {"display": 0},
        "Feedback": {"display": 0}, "Freeze": {"item": "Off"},
        "Filter On": {"item": "Off"}, "Filter Freq": {"display": 1000}, "Filter Width": {"display": 8},
        "LFO > Delay": {"display": 0}, "LFO > Filter": {"display": 0},
        "LFO Mode": {"item": "Rate"}, "LFO Freq": {"display": 1}, "LFO Wave": {"item": "Sine"},
        "LFO Morph": {"display": 0}, "Dry/Wet": {"display": 100}}

SYNC = dict(BASE, **{"L Sync": {"item": "On"}, "R Sync": {"item": "On"}})


def sixteenth(left, right):
    return {"L 16th": {"item": str(left)}, "R 16th": {"item": str(right)}}


RUNS = [
    {"name": "delay-offset", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "whether Offset scales the whole synced delay or one sixteenth, and its range (tap times at +-33 and +-17 %)",
     "question": "impulse taps for Sync 4 (500 ms) with Offset L +33 / R -33 %, +-17 %, and Sync 8 (1 s) with +-33 %",
     "base": SYNC,
     "cases": [["four-pm33", dict(sixteenth(4, 4), **{"L Offset": {"display": 33}, "R Offset": {"display": -33}})],
               ["four-pm17", dict(sixteenth(4, 4), **{"L Offset": {"display": 17}, "R Offset": {"display": -17}})],
               ["eight-pm33", dict(sixteenth(8, 8), **{"L Offset": {"display": 33}, "R Offset": {"display": -33}})],
               ["one-p33", dict(sixteenth(1, 1), **{"L Offset": {"display": 33}, "R Offset": {"display": -33}})]]},

    {"name": "delay-feedback", "plan": "4", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "repeat-to-repeat ratio against Feedback up to 95 %, and whether the band-pass sits inside the loop (tap shapes and levels)",
     "question": "tap levels (up to 16) for Feedback 25, 50, 75, 95 % with the filter off, and 50 % with the filter on at 1 kHz Width 8, delay 100 ms both",
     "base": dict(BASE, **{"R Time": {"display": 0.1}}),
     "cases": [[f"fb-{f}", {"Feedback": {"display": f}}] for f in (25, 50, 75, 95)] +
              [["fb-50-filter", {"Feedback": {"display": 50}, "Filter On": {"item": "On"}}],
               ["fb-50-filter-narrow", {"Feedback": {"display": 50}, "Filter On": {"item": "On"},
                                        "Filter Width": {"display": 1}}]]},

    {"name": "delay-filter", "plan": "5", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "the band-pass in front of the lines: centre, bandwidth against Width, slope, range ends (noise spectrum and sweep of the delayed signal)",
     "question": "noise/sweep response with Filter on for Freq 200 Hz, 1 kHz, 5 kHz at Width 4 and Width 1 and 9 at 1 kHz, Feedback 0",
     "base": dict(BASE, **{"Filter On": {"item": "On"}}),
     "cases": [["f200-w4", {"Filter Freq": {"display": 200}, "Filter Width": {"display": 4}}],
               ["f1000-w4", {"Filter Width": {"display": 4}}],
               ["f5000-w4", {"Filter Freq": {"display": 5000}, "Filter Width": {"display": 4}}],
               ["f1000-w1", {"Filter Width": {"display": 1}}],
               ["f1000-w9", {"Filter Width": {"display": 9}}],
               ["f50-w4", {"Filter Freq": {"display": 50}, "Filter Width": {"display": 4}}]]},

    {"name": "delay-lfo-delay", "plan": "6, 7", "probe": "gap2", "read": ["modulation", "envelope"],
     "priority": 1,
     "why": "LFO > Delay depth in ms (absolute or relative to the delay time) and what Repitch, Fade and Jump do to the delayed tone",
     "question": "FM depth/rate and envelope of the steady tone for LFO > Delay 100 % at 100/200 ms and 300 ms, 25 and 50 % at 300 ms (Repitch), and Fade and Jump at 300 ms",
     "base": dict(BASE, **{"LFO > Delay": {"display": 100}}),
     "cases": [["d100-200-a100", {}], ["d300-a100", {"L Time": {"display": 0.3}, "R Time": {"display": 0.3}}],
               ["d300-a50", {"L Time": {"display": 0.3}, "R Time": {"display": 0.3}, "LFO > Delay": {"display": 50}}],
               ["d300-a25", {"L Time": {"display": 0.3}, "R Time": {"display": 0.3}, "LFO > Delay": {"display": 25}}],
               ["d300-fade", {"L Time": {"display": 0.3}, "R Time": {"display": 0.3}, "Smoothing": {"item": "Fade"}}],
               ["d300-jump", {"L Time": {"display": 0.3}, "R Time": {"display": 0.3}, "Smoothing": {"item": "Jump"}}]]},

    {"name": "delay-lfo-filter", "plan": "6", "probe": "gap2", "read": ["modulation", "envelope"],
     "priority": 2,
     "why": "LFO > Filter depth in octaves: the band-pass sweeps across the steady 1 kHz tone, so the AM trace gives the excursion",
     "question": "AM depth/trace of the steady tone through a Width 4 band-pass at 2 kHz for LFO > Filter 25, 50, 100 % (sine, 1 Hz)",
     "base": dict(BASE, **{"Filter On": {"item": "On"}, "Filter Freq": {"display": 2000}, "Filter Width": {"display": 4}}),
     "cases": [[f"filter-{a}", {"LFO > Filter": {"display": a}}] for a in (25, 50, 100)]},

    {"name": "delay-lfo-waves", "plan": "6", "probe": "gap2", "read": ["modulation", "envelope"],
     "priority": 2,
     "why": "the LFO shapes (and Morph) as pitch against time of the delayed tone",
     "question": "FM trace of the steady tone for LFO Wave Triangle, Ramp Up, Ramp Down, Square, S & H, Wander, and Triangle with Morph +-100 % (Sine is the default case)",
     "base": dict(BASE, **{"LFO > Delay": {"display": 100}, "L Time": {"display": 0.3}, "R Time": {"display": 0.3}}),
     "cases": [[f"wave-{w.lower().replace(' & ', 'n').replace(' ', '-')}", {"LFO Wave": {"item": w}}]
               for w in ("Triangle", "Ramp Up", "Ramp Down", "Square", "S & H", "Wander")] +
              [["triangle-morph-p100", {"LFO Wave": {"item": "Triangle"}, "LFO Morph": {"display": 100}}],
               ["triangle-morph-m100", {"LFO Wave": {"item": "Triangle"}, "LFO Morph": {"display": -100}}]]},

    {"name": "delay-time", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "delay time against the Sync buttons and against the typed Time (1 ms to 1 s), including the minimum and any fixed offset",
     "question": "impulse taps for Sync (1,2), (3,4), (5,6), (8,3) sixteenths and Time (1,3), (20,50), (250,500), (750,1000) ms at 120 BPM",
     "base": BASE,
     "cases": [["sync-1-2", dict(sixteenth(1, 2), **{"L Sync": {"item": "On"}, "R Sync": {"item": "On"}})],
               ["sync-3-4", dict(sixteenth(3, 4), **{"L Sync": {"item": "On"}, "R Sync": {"item": "On"}})],
               ["sync-5-6", dict(sixteenth(5, 6), **{"L Sync": {"item": "On"}, "R Sync": {"item": "On"}})],
               ["sync-8-3", dict(sixteenth(8, 3), **{"L Sync": {"item": "On"}, "R Sync": {"item": "On"}})],
               ["ms-1-3", {"L Time": {"display": 0.001}, "R Time": {"display": 0.003}}],
               ["ms-20-50", {"L Time": {"display": 0.02}, "R Time": {"display": 0.05}}],
               ["ms-250-500", {"L Time": {"display": 0.25}, "R Time": {"display": 0.5}}],
               ["ms-750-1000", {"L Time": {"display": 0.75}, "R Time": {"display": 1.0}}]]},

    {"name": "delay-pingpong", "plan": "8", "probe": "gap2", "read": ["impulse", "stereo"], "priority": 2,
     "why": "the Ping Pong pattern: channel of each repeat, spacing with equal and unequal times, with a one-sided tone (left, right segments)",
     "question": "impulse taps and L/R tone levels for Ping Pong off/on at 250 ms both, on with 200/300 ms, and on with Feedback 50 %",
     "base": dict(BASE, **{"L Time": {"display": 0.25}, "R Time": {"display": 0.25}, "Feedback": {"display": 50}}),
     "cases": [["pp-on", {"Ping Pong": {"item": "On"}}],
               ["pp-on-unequal", {"Ping Pong": {"item": "On"}, "L Time": {"display": 0.2}, "R Time": {"display": 0.3}}],
               ["pp-on-fb-0", {"Ping Pong": {"item": "On"}, "Feedback": {"display": 0}}]]},

    {"name": "delay-drywet", "plan": "10", "probe": "gap2", "read": ["modulation", "static", "impulse"],
     "priority": 2,
     "why": "the Dry/Wet law (linear or equal-power) from the level of a tone delayed by a whole number of cycles (100 ms of 1 kHz), and the dry tap level",
     "question": "level of the steady tone and tap levels for Dry/Wet 0, 25, 50, 75 % (100 % is the default case); delay 100 ms, Feedback 0",
     "base": dict(BASE, **{"R Time": {"display": 0.1}}),
     "cases": [[f"wet-{w}", {"Dry/Wet": {"display": w}}] for w in (0, 25, 50, 75)]},
]
