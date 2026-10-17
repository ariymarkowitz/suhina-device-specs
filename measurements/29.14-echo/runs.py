# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Echo behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.14-echo.md > Measurement plan.

The impulse (one sample at time 0, both channels) reads delay times and repeats (up to 16 taps
per channel); the steady tone and bursts read modulation (FM / AM), gating and ducking; the
silence segment reads Noise. Left and right are set to different times so one render reads both.
Stereo Link is off, with both channels set explicitly. Tempo is 120 BPM (a quarter note is
500 ms). Static runs set Repitch off so a value set through the set cannot be glided to; the
modulation run compares Repitch on and off. Times stay at or below 1 s so the repeats fit the 2 s
gap.

Not taken: Auto-off after 8 s of silence (step 13: needs a long silent input and CPU readings),
stepping the delay time to measure the Repitch glide (step 11: no parameter changes during the
render), Repitch Smoothing Time (the same reason), switching Channel Mode live, the 2.5 s top
of the time range (longer than the gap), Equal-Loudness (a context-menu option), and long reverb
tails beyond 2 s (the Reverb run keeps Decay at or below 50 %)."""

DEVICE = "Echo"

# Stereo, Time mode (L 100 ms, R 200 ms), no feedback, filter/gate/ducking/noise/wobble/reverb/
# modulation off, Repitch off, 100 % wet.
BASE = {"Channel Mode": {"item": "Stereo"}, "Link": {"item": "Off"}, "Repitch": {"item": "Off"},
        "L Sync": {"item": "Off"}, "R Sync": {"item": "Off"},
        "L Time": {"display": 0.1}, "R Time": {"display": 0.2},
        "L Sync Mode": {"item": "Synced"}, "R Sync Mode": {"item": "Synced"},
        "L Offset": {"display": 0}, "R Offset": {"display": 0},
        "Feedback": {"display": 0}, "FB Invert": {"item": "Off"},
        "Input Gain": {"display": 0}, "Clip Dry": {"item": "Off"},
        "Filter On": {"item": "Off"}, "Gate On": {"item": "Off"}, "Duck On": {"item": "Off"},
        "Noise On": {"item": "Off"}, "Wobble On": {"item": "Off"},
        "Mod Sync": {"item": "Off"}, "Mod Freq": {"display": 1}, "Mod Wave": {"item": "Sine"},
        "Mod Phase": {"display": 90}, "Dly < Mod": {"display": 0}, "Flt < Mod": {"display": 0},
        "Mod 4x": {"item": "Off"}, "Env Mix": {"display": 0},
        "Reverb Level": {"display": 0}, "Reverb Loc": {"item": "Post"}, "Reverb Decay": {"display": 50},
        "Stereo Width": {"display": 100}, "Output": {"display": 0}, "Dry Wet": {"display": 100}}

SYNC = dict(BASE, **{"L Sync": {"item": "On"}, "R Sync": {"item": "On"}})

# Synced division values: -6 1/64, -5 1/32, -4 1/16, -3 1/8, -2 1/4, -1 1/2, 0 1 (bar).
EIGHTH, QUARTER, HALF = -3, -2, -1

RUNS = [
    {"name": "echo-sync", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "delay time for each Sync Mode: Synced divisions, Triplet (x2/3), Dotted (x1.5) and the 16th count",
     "question": "impulse taps for Synced 1/8 | 1/4, Triplet 1/8 | 1/4, Dotted 1/8 | 1/4, 16th 3 | 5 and Synced 1/16 | 1/2 (left | right)",
     "base": SYNC,
     "cases": [["synced-8-4", {"L Synced": EIGHTH, "R Synced": QUARTER}],
               ["triplet-8-4", {"L Sync Mode": {"item": "Triplet"}, "R Sync Mode": {"item": "Triplet"},
                                "L Synced": EIGHTH, "R Synced": QUARTER}],
               ["dotted-8-4", {"L Sync Mode": {"item": "Dotted"}, "R Sync Mode": {"item": "Dotted"},
                               "L Synced": EIGHTH, "R Synced": QUARTER}],
               ["sixteenth-3-5", {"L Sync Mode": {"item": "16th"}, "R Sync Mode": {"item": "16th"},
                                  "L 16th": 3, "R 16th": 5}],
               ["synced-16-2", {"L Synced": -4, "R Synced": HALF}]]},

    {"name": "echo-time-offset", "plan": "3", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "delay time against the typed Time (minimum, mid, 1 s) and whether Offset scales the whole synced delay or a sixteenth (+-33 %, +-17 %)",
     "question": "impulse taps for Time (1, 3), (20, 50), (750, 1000) ms and Sync 1/4 with Offset L +33 / R -33 % and +-17 %",
     "base": BASE,
     "cases": [["ms-1-3", {"L Time": {"display": 0.001}, "R Time": {"display": 0.003}}],
               ["ms-20-50", {"L Time": {"display": 0.02}, "R Time": {"display": 0.05}}],
               ["ms-750-1000", {"L Time": {"display": 0.75}, "R Time": {"display": 1.0}}],
               ["quarter-pm33", dict(SYNC, **{"L Synced": QUARTER, "R Synced": QUARTER,
                                                "L Offset": {"display": 33}, "R Offset": {"display": -33}})],
               ["quarter-pm17", dict(SYNC, **{"L Synced": QUARTER, "R Synced": QUARTER,
                                                "L Offset": {"display": 17}, "R Offset": {"display": -17}})]]},

    {"name": "echo-feedback", "plan": "5, 4", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "repeat ratio against Feedback including above 100 % (does the loop limit?), Invert's polarity, and whether the filter sits in the loop",
     "question": "tap levels (up to 16) at 100 ms for Feedback 50, 100, 150 %, 100 % inverted, and 50 % with the default filter on",
     "base": dict(BASE, **{"R Time": {"display": 0.1}}),
     "cases": [["fb-50", {"Feedback": {"display": 50}}], ["fb-100", {"Feedback": {"display": 100}}],
               ["fb-150", {"Feedback": {"display": 150}}],
               ["fb-100-invert", {"Feedback": {"display": 100}, "FB Invert": {"item": "On"}}],
               ["fb-50-filter", {"Feedback": {"display": 50}, "Filter On": {"item": "On"},
                                 "HP Freq": {"display": 500}, "LP Freq": {"display": 2000}}]]},

    {"name": "echo-filter", "plan": "4", "probe": "gap2", "read": ["response"], "priority": 1,
     "why": "the high-pass and low-pass: cutoff, slope and resonance (HP Res, LP Res up to 0.30)",
     "question": "noise/sweep response of the wet path for HP 100 and 1000 Hz, LP 500 and 5000 Hz, and HP 500 Hz / LP 2 kHz with Res 0.30",
     "base": dict(BASE, **{"Filter On": {"item": "On"}, "HP Freq": {"display": 20}, "LP Freq": {"display": 20000},
                           "HP Res": {"display": 0}, "LP Res": {"display": 0}}),
     "cases": [["hp-100", {"HP Freq": {"display": 100}}], ["hp-1000", {"HP Freq": {"display": 1000}}],
               ["lp-500", {"LP Freq": {"display": 500}}], ["lp-5000", {"LP Freq": {"display": 5000}}],
               ["hp-500-res", {"HP Freq": {"display": 500}, "HP Res": {"display": 0.3}}],
               ["lp-2000-res", {"LP Freq": {"display": 2000}, "LP Res": {"display": 0.3}}]]},

    {"name": "echo-gate-duck", "plan": "7", "probe": "gap2", "read": ["dynamics", "static"], "priority": 2,
     "why": "Gate: threshold and release on the -30 and -6 dBFS bursts; Ducking: how far the wet path drops against input level (staircase) and how long it takes to recover",
     "question": "bursts through Gate -20 dB at Release 50 ms and 500 ms; staircase wet gain with Ducking at -30 and -10 dB, Release 100 ms and 1 s (Feedback 0, 100 ms)",
     "base": BASE,
     "cases": [["gate-20-r50", {"Gate On": {"item": "On"}, "Gate Thr": {"display": -20}, "Gate Release": {"display": 0.05}}],
               ["gate-20-r500", {"Gate On": {"item": "On"}, "Gate Thr": {"display": -20}, "Gate Release": {"display": 0.5}}],
               ["duck-30", {"Duck On": {"item": "On"}, "Duck Thr": {"display": -30}}],
               ["duck-10", {"Duck On": {"item": "On"}, "Duck Thr": {"display": -10}}],
               ["duck-30-r1000", {"Duck On": {"item": "On"}, "Duck Thr": {"display": -30}, "Duck Release": {"display": 1}}]]},

    {"name": "echo-mod-delay", "plan": "8, 11", "probe": "gap2", "read": ["modulation", "stereo"], "priority": 2,
     "why": "Mod Delay depth (cents of the delayed tone), x4, L/R Phase, and Repitch on vs off (vibrato or crossfade steps)",
     "question": "FM depth/rate and L/R correlation of the steady tone: Mod Delay 100 and 50 % at 300 ms, x4, Phase 0 and 180, Repitch on",
     "base": dict(BASE, **{"L Time": {"display": 0.3}, "R Time": {"display": 0.3}, "Dly < Mod": {"display": 100}}),
     "cases": [["mod-50", {"Dly < Mod": {"display": 50}}], ["mod-100-x4", {"Mod 4x": {"item": "On"}}],
               ["phase-0", {"Mod Phase": {"display": 0}}], ["phase-180", {"Mod Phase": {"display": 180}}],
               ["repitch-on", {"Repitch": {"item": "On"}}],
               ["wave-square", {"Mod Wave": {"item": "Square"}}], ["wave-random", {"Mod Wave": {"item": "Random"}}]]},

    {"name": "echo-mod-filter-env", "plan": "8", "probe": "gap2", "read": ["modulation", "envelope"], "priority": 2,
     "why": "Mod Filter depth (the swept low-pass crossing the steady 1 kHz tone) and Env Mix: the envelope follower's modulation against the LFO",
     "question": "AM trace of the steady tone through LP 1 kHz for Flt<Mod 25, 50, 100 %, and with Env Mix 100 % (bursts) for Flt<Mod and Dly<Mod",
     "base": dict(BASE, **{"Filter On": {"item": "On"}, "HP Freq": {"display": 20}, "LP Freq": {"display": 1000},
                           "Flt < Mod": {"display": 100}}),
     "cases": [["flt-25", {"Flt < Mod": {"display": 25}}], ["flt-50", {"Flt < Mod": {"display": 50}}],
               ["env-flt-100", {"Env Mix": {"display": 100}}],
               ["env-dly-100", {"Env Mix": {"display": 100}, "Flt < Mod": {"display": 0}, "Dly < Mod": {"display": 100},
                                "L Time": {"display": 0.3}, "R Time": {"display": 0.3}}]]},

    {"name": "echo-noise-wobble", "plan": "9", "probe": "gap2", "read": ["silence", "modulation"], "priority": 3,
     "why": "the Noise floor (level and type against Amount and Morph, from the silent segment) and Wobble's pitch deviation (FM of the steady tone)",
     "question": "noise level/spectrum for Noise 50 % and 100 % at Morph 0, 100 %; FM statistics for Wobble 50 and 100 % at Morph 0 and 100 %",
     "base": dict(BASE, **{"L Time": {"display": 0.3}, "R Time": {"display": 0.3}}),
     "cases": [["noise-50", {"Noise On": {"item": "On"}, "Noise Amt": {"display": 50}}],
               ["noise-100-m0", {"Noise On": {"item": "On"}, "Noise Amt": {"display": 100}, "Noise Mrph": {"display": 0}}],
               ["noise-100-m100", {"Noise On": {"item": "On"}, "Noise Amt": {"display": 100}, "Noise Mrph": {"display": 100}}],
               ["wobble-50", {"Wobble On": {"item": "On"}, "Wobble Amt": {"display": 50}}],
               ["wobble-100-m0", {"Wobble On": {"item": "On"}, "Wobble Amt": {"display": 100}, "Wobble Mrph": {"display": 0}}],
               ["wobble-100-m100", {"Wobble On": {"item": "On"}, "Wobble Amt": {"display": 100}, "Wobble Mrph": {"display": 100}}]]},

    {"name": "echo-reverb", "plan": "10", "probe": "gap2", "read": ["impulse"], "priority": 2,
     "why": "the built-in reverb: its place in the chain (Pre, Post, Feedback), level law and Decay (impulse response)",
     "question": "impulse response at Reverb 50 % with Pre, Post, Feedback (Feedback 50 %), Decay 25 % and 50 %, and Reverb 100 % Post",
     "base": dict(BASE, **{"Reverb Level": {"display": 50}}),
     "cases": [["pre", {"Reverb Loc": {"item": "Pre"}}],
               ["post", {"Reverb Loc": {"item": "Post"}}],
               ["feedback", {"Reverb Loc": {"item": "Feedback"}, "Feedback": {"display": 50}}],
               ["post-decay-25", {"Reverb Decay": {"display": 25}}],
               ["post-level-100", {"Reverb Level": {"display": 100}}]]},

    {"name": "echo-channel-stereo", "plan": "10", "probe": "gap2", "read": ["impulse", "stereo"], "priority": 2,
     "why": "Ping Pong and Mid/Side routing (which channel each repeat falls in, with a one-sided tone) and the Stereo width law on the wet signal",
     "question": "impulse taps and 2x2 level matrix for Ping Pong and Mid/Side (Feedback 50 %, 150 | 300 ms), and Stereo 0 and 200 % in Stereo mode",
     "base": dict(BASE, **{"L Time": {"display": 0.15}, "R Time": {"display": 0.3}, "Feedback": {"display": 50}}),
     "cases": [["ping-pong", {"Channel Mode": {"item": "Ping Pong"}}],
               ["mid-side", {"Channel Mode": {"item": "Mid/Side"}}],
               ["mid-side-width-0", {"Channel Mode": {"item": "Mid/Side"}, "Stereo Width": {"display": 0}}],
               ["width-0", {"Stereo Width": {"display": 0}}], ["width-200", {"Stereo Width": {"display": 200}}]]},

    {"name": "echo-input-mix", "plan": "6, 12", "probe": "gap2", "read": ["static", "impulse"], "priority": 3,
     "why": "Input gain on the wet path, D (Clip Dry) distorting the dry path at +20 dB, Output's dB law, and the Dry/Wet law (dry share at 50 %)",
     "question": "staircase level/THD at Dry/Wet 50 % for Input +10 dB, +20 dB with D off/on, Output -12 dB, and Dry/Wet 25 %",
     "base": dict(BASE, **{"Dry Wet": {"display": 50}}),
     "cases": [["in-p10", {"Input Gain": {"display": 10}}],
               ["in-p20", {"Input Gain": {"display": 20}}],
               ["in-p20-d", {"Input Gain": {"display": 20}, "Clip Dry": {"item": "On"}}],
               ["out-m12", {"Output": {"display": -12}}],
               ["wet-25", {"Dry Wet": {"display": 25}}]]},
]
