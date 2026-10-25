# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Filter Delay behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.19-filter-delay.md > Measurement plan.

The base uses delay 2 alone (pan centre, 0 dB, feedback 0, filter off, free time of 1 ms), Dry
at -inf, so the wet path of one line is isolated. The longest times are 1 s, so the 2 s gap of the
probe holds every echo.

Not measurable this way: plan 7 (pitch glide or crossfade when the time changes needs automation);
the filter-in-the-loop narrowing of plan 4 is only seen through the impulse response of
filter-delay-feedback (no change over time can be made)."""

DEVICE = "Filter Delay"

INF = {"norm": 0.0}
BASE = {
    "1 Input On": {"item": "Off"}, "3 Input On": {"item": "Off"}, "2 Input On": {"item": "On"},
    "2 Filter On": {"item": "Off"}, "2 Delay Mode": {"item": "Off"},
    "2 Time Delay": {"display": 0.001}, "2 Feedback": {"display": 0},
    "2 Volume": {"display": 0}, "2 Pan": 0, "Dry": INF,
}


def sync(beat, swing=0):
    return {"2 Delay Mode": {"item": "On"}, "2 Beat Delay": {"item": str(beat)}, "2 Beat Swing": {"display": swing}}


RUNS = [
    {"name": "filter-delay-time", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "free delay time accuracy over the 1 to 999 ms range (incl. any fixed offset at 1 ms)",
     "question": "Sync off, Delay Time 1 (the default case), 10, 100, 500 and 999 ms, feedback 0, filter off",
     "base": BASE,
     "cases": [[f"ms-{v}", {"2 Time Delay": {"display": v / 1000}}] for v in (10, 100, 500, 999)]},

    {"name": "filter-delay-sync", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "synced time per button at 120 BPM, and how the swing field scales it (whole delay or one step)",
     "question": "Sync on, buttons 1, 3, 5 and 8 sixteenths; button 4 with swing +33.3, -33.3 and +16.7 %",
     "base": BASE,
     "cases": [[f"beat-{b}", sync(b)] for b in (1, 3, 5, 8)] + [
         ["beat-4-sw+33", sync(4, 33.3)],
         ["beat-4-sw-33", sync(4, -33.3)],
         ["beat-4-sw+17", sync(4, 16.7)],
     ]},

    {"name": "filter-delay-filter", "plan": "3", "probe": "gap2", "read": ["response.sweep_db", "response.noise_db"], "priority": 1,
     "why": "the X-Y pad's band-pass: centre, -3 dB points, slope and the unit of Width (octaves?), against Filter On off",
     "question": "wet path only with the filter off, and at 1 kHz with Width 0.5, 4 and 9, 100 Hz and 10 kHz at Width 4, 50 Hz at Width 1",
     "base": BASE | {"2 Filter On": {"item": "On"}},
     "cases": [
         ["off", {"2 Filter On": {"item": "Off"}}],
         ["f1k-w0.5", {"2 Filter Freq": {"display": 1000}, "2 Filter Width": 0.5}],
         ["f1k-w4", {"2 Filter Freq": {"display": 1000}, "2 Filter Width": 4}],
         ["f1k-w9", {"2 Filter Freq": {"display": 1000}, "2 Filter Width": 9}],
         ["f100-w4", {"2 Filter Freq": {"display": 100}, "2 Filter Width": 4}],
         ["f10k-w4", {"2 Filter Freq": {"display": 10000}, "2 Filter Width": 4}],
         ["f50-w1", {"2 Filter Freq": {"display": 50}, "2 Filter Width": 1}],
     ]},

    {"name": "filter-delay-feedback", "plan": "4", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "echo ratio against Feedback (including 100 % and any limit), and the filter's effect on the repeats",
     "question": "delay of 100 ms, Feedback 25, 50, 75 and 100 %, and 50 % with the filter at 1 kHz Width 4 in the loop",
     "base": BASE | {"2 Time Delay": {"display": 0.1}},
     "cases": [[f"fb-{v}", {"2 Feedback": {"display": v}}] for v in (25, 50, 75, 100)] + [
         ["fb-50-filter", {"2 Feedback": {"display": 50}, "2 Filter On": {"item": "On"},
                           "2 Filter Freq": {"display": 1000}, "2 Filter Width": 4}],
     ]},

    {"name": "filter-delay-pan", "plan": "5", "probe": "gap2", "read": ["stereo"], "priority": 2,
     "why": "the Pan law (linear or equal power) from the 2x2 level matrix, and the level at centre",
     "question": "delay 2 with Pan 50L, 25L, C (the default case), 25R and 50R, wet only",
     "base": BASE,
     "cases": [[f"pan-{n}", {"2 Pan": v}] for n, v in (("L50", -1), ("L25", -0.5), ("R25", 0.5), ("R50", 1))]},

    {"name": "filter-delay-levels", "plan": "5", "probe": "gap2", "read": ["static"], "priority": 2,
     "why": "Volume and Dry in real dB against their displays, -inf, and the line's gain at 0 dB",
     "question": "delay 2 Volume +6, -20 dB and -inf; and the dry path alone at 0 and -20 dB (delay off)",
     "base": BASE,
     "cases": [
         ["vol+6", {"2 Volume": {"display": 6}}],
         ["vol-20", {"2 Volume": {"display": -20}}],
         ["vol-inf", {"2 Volume": INF}],
         ["dry-0", {"2 Input On": {"item": "Off"}, "Dry": {"display": 0}}],
         ["dry-20", {"2 Input On": {"item": "Off"}, "Dry": {"display": -20}}],
     ]},

    {"name": "filter-delay-routing", "plan": "6", "probe": "gap2", "read": ["stereo"], "priority": 2,
     "why": "which input channel each of the three delays takes (delay 2 the sum?)",
     "question": "each delay alone with Pan centre; read the L/R matrix of the one-channel sines",
     "base": BASE | {"1 Pan": 0, "3 Pan": 0, "1 Filter On": {"item": "Off"}, "3 Filter On": {"item": "Off"},
                     "1 Delay Mode": {"item": "Off"}, "3 Delay Mode": {"item": "Off"},
                     "1 Time Delay": {"display": 0.001}, "3 Time Delay": {"display": 0.001},
                     "1 Feedback": {"display": 0}, "3 Feedback": {"display": 0},
                     "1 Volume": {"display": 0}, "3 Volume": {"display": 0}},
     "cases": [
         ["d1-only", {"1 Input On": {"item": "On"}, "2 Input On": {"item": "Off"}}],
         ["d3-only", {"3 Input On": {"item": "On"}, "2 Input On": {"item": "Off"}}],
     ]},

    # ---- third set (measurements/third/): the time changed by a lane; the stored element
    # DelayTransitionMode (1 in the loaded device) may choose how a change sounds
    {"name": "filter-delay-time-jump", "plan": "7", "probe": "gap2", "read": ["raw render around the jump (pitch glide or crossfade)"], "priority": 1,
     "why": "what a delay-time change does to the sound (pitch glide or crossfade), and the stored transition mode",
     "question": "the steady tone's echo around 2 Time Delay jumping from 100 to 200 ms at beat 46 (23 s), DelayTransitionMode 1 and 0",
     "base": dict(BASE, **{"2 Time Delay": {"auto": [[0, {"display": 0.1}], [46, {"display": 0.1}], [46, {"display": 0.2}]]}}),
     "cases": [["mode1", {"@DelayTransitionMode": 1}], ["mode0", {"@DelayTransitionMode": 0}]]},

    # ---- fifth set: the same change on the noise (a 1 kHz tone hides a shift of a whole number of
    # cycles), with every value of the stored mode (0 and 1 were read in the third set; 2 is new)
    {"name": "filter-delay-time-step-noise", "plan": "7", "probe": "gap2", "read": ["raw render around the step (pitch, crossfade, discontinuity)"], "priority": 2,
     "why": "the third set's tone read modes 0 and 1 as a pitch glide and a short crossfade, but a 100 ms step is invisible on a 1 kHz tone, and the third stored mode was not run",
     "question": "the noise's echo around 2 Time Delay stepping from 100 to 200 ms at beat 64 (32 s), DelayTransitionMode 0, 1 and 2",
     "base": dict(BASE, **{"2 Time Delay": {"auto": [[0, {"display": 0.1}], [64, {"display": 0.1}], [64, {"display": 0.2}]]}}),
     "cases": [[f"mode{m}", {"@DelayTransitionMode": m}] for m in (0, 1, 2)]},

    {"name": "filter-delay-time-ramp-noise", "plan": "7", "probe": "gap2", "read": ["raw render around the ramp (local delay against time)"], "priority": 2,
     "why": "a ramp is what Repitch glides over and Fade crosses; the step in filter-delay-time-step-noise only shows the splice",
     "question": "the noise's echo while 2 Time Delay ramps from 100 to 200 ms over the 2.75 s from beat 64 (32 s) to beat 69.5, DelayTransitionMode 0, 1 and 2",
     "base": dict(BASE, **{"2 Time Delay": {"auto": [[0, {"display": 0.1}], [64, {"display": 0.1}], [69.5, {"display": 0.2}]]}}),
     "cases": [[f"mode{m}", {"@DelayTransitionMode": m}] for m in (0, 1, 2)]},
]
