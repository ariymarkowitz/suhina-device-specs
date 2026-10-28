# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Beat Repeat behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.05-beat-repeat.md > Measurement plan.

How the probe is used. At 120 BPM a bar is 2 s, and the probe starts at a bar line, so Interval
1 Bar triggers at the start of the probe. The probe's impulse (one sample at time 0) is then
inside the first captured slice and every repeat of that slice shows as a tap: the taps' times
give the repeat spacing (Grid, and how Pitch stretches it) and their levels give Decay, Volume
and Pitch Decay. The steady 1 kHz tone (8 s) and the staircase show the windows when repeats play
(Mix Type Gate leaves only the repeats), so the start, the length and the crossfades are read
from their envelope; the noise (4 s) gives the filter's response during repeats. All of these
read the renders directly (analyse.py's `impulse` taps stop at 16 and may need a second look at
the .ir.wav and the envelope files). Cases use Mix Type Gate unless the run is about Mix modes.

Not taken: Chance statistics over many bars (plan step 4: the probe has ~23 bars, one render
per case; a few cases at 50 % would only show one random draw), Variation statistics beyond
one draw per mode (beatrepeat-variation is a snapshot), tempo change or transport stop during
repeats, the unit of Width beyond the filter run's noise spectrum."""

DEVICE = "Beat Repeat"

# Indices (internal values) of the stepped lists.
INTERVAL = {"1/32": 0, "1/16": 1, "1/8": 2, "1/4": 3, "1/2": 4, "1 Bar": 5, "2 Bar": 6, "4 Bar": 7}
GRID = {"1/256": 0, "1/128": 1, "1/96": 2, "1/64": 3, "1/48": 4, "1/32": 5, "1/24": 6, "1/16": 7,
        "1/12": 8, "1/8": 9, "1/6": 10, "1/4": 11, "1/3": 12, "1/2": 13, "3/4": 14, "1 Bar": 15}
# Gate: n/16 is index n-1 for n = 1..15, then 1 Bar .. 4 Bar are 15..18.

# Trigger at the start of every bar, Grid 1/16, repeats for the whole bar, only repeats heard.
BASE = {"Chance": {"display": 100}, "Interval": INTERVAL["1 Bar"], "Offset": 0, "Grid": GRID["1/16"],
        "Block Triplets": {"item": "Off"}, "Variation": 0, "Variation Type": {"item": "Trigger"},
        "Gate": 15, "Decay": {"display": 0}, "Pitch Decay": {"display": 0}, "Pitch": 0,
        "Mix Type": {"item": "Gate"}, "Volume": {"display": 0}, "Filter On": {"item": "Off"},
        "Repeat": {"item": "Off"}}


def gid(name):
    return name.replace("/", "-").replace(" ", "").lower()


RUNS = [
    {"name": "beatrepeat-grid", "plan": "2", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "repeat spacing for Grid values incl. triplets, from the taps of the captured impulse; where the first repeat begins",
     "question": "impulse taps (time, level) for Grid 1/32, 1/16, 1/8, 1/6, 1/4, 1/3 with Interval 1 Bar and Gate 1 Bar",
     "base": BASE,
     "cases": [[f"grid-{gid(g)}", {"Grid": GRID[g]}] for g in ("1/32", "1/8", "1/6", "1/4", "1/3")]},

    {"name": "beatrepeat-gate", "plan": "2", "probe": "gap2", "read": ["impulse", "modulation"],
     "priority": 1,
     "why": "total repeat length from Gate, including the Gate <= Grid rule (nothing repeats), seen as the last tap and the end of the repeat window",
     "question": "impulse taps and steady-tone window for Gate 1/16 (= Grid), 2/16, 4/16, 8/16 and 2 Bar (the default case is 1 Bar)",
     "base": BASE,
     "cases": [[f"gate-{n}-16", {"Gate": n - 1}] for n in (1, 2, 4, 8)] + [["gate-2bar", {"Gate": 16}]]},

    {"name": "beatrepeat-trigger", "plan": "2, 3, 10", "probe": "gap2", "read": ["modulation", "static", "dynamics"],
     "priority": 1,
     "why": "when repeats start: Interval, Offset, the Repeat button and Chance 0 (steady-tone window position; staircase level shows which slice is captured)",
     "question": "start and length of the repeat window in the steady tone and staircase for Interval 1/2 and 1/4, Offset 8/16, Repeat on, Chance 0 %; Gate 4/16, Grid 1/16",
     "base": dict(BASE, **{"Gate": 3}),
     "cases": [["bar-offset-8", {"Offset": 8}], ["bar-offset-4", {"Offset": 4}],
               ["interval-half", {"Interval": INTERVAL["1/2"]}],
               ["interval-quarter", {"Interval": INTERVAL["1/4"]}],
               ["chance-0", {"Chance": {"display": 0}}],
               ["repeat-chance-0", {"Chance": {"display": 0}, "Repeat": {"item": "On"}}]]},

    {"name": "beatrepeat-decay-volume", "plan": "7", "probe": "gap2", "read": ["impulse"], "priority": 1,
     "why": "level of each repeat against Decay (curve per repeat) and Volume's dB law, from the tap levels",
     "question": "tap levels for Decay 0 (default), 25, 50, 100 % and Volume -6, -12, +6 dB",
     "base": BASE,
     "cases": [[f"decay-{d}", {"Decay": {"display": d}}] for d in (25, 50, 100)] +
              [[f"volume-{n}", {"Volume": {"display": v}}]
               for n, v in (("m12", -12), ("m6", -6), ("p6", 6))]},

    {"name": "beatrepeat-pitch", "plan": "6", "probe": "gap2", "read": ["impulse", "modulation"],
     "priority": 2,
     "why": "Pitch (resampling: tap spacing and tone frequency of each repeat) and Pitch Decay's per-repeat drop",
     "question": "tap spacing and tone frequency of repeats for Pitch -3, -7, -12 st and Pitch Decay 50, 100 % at Pitch 0 and -12",
     "base": dict(BASE, **{"Grid": GRID["1/8"]}),
     "cases": [[f"pitch-m{p}", {"Pitch": p}] for p in (3, 7, 12)] +
              [["pdecay-50", {"Pitch Decay": {"display": 50}}], ["pdecay-100", {"Pitch Decay": {"display": 100}}],
               ["pdecay-50-pitch-m12", {"Pitch Decay": {"display": 50}, "Pitch": 12}]]},

    {"name": "beatrepeat-filter", "plan": "8", "probe": "gap2", "read": ["response"], "priority": 2,
     "why": "the repeat filter's band: centre, slope and what Width means (noise spectrum while repeating)",
     "question": "noise spectrum of the repeats for Freq 200 Hz, 1 kHz, 5 kHz at Width 4, and Width 1 and 9 at 1 kHz, Filter On",
     "base": dict(BASE, **{"Filter On": {"item": "On"}, "Grid": GRID["1/4"]}),
     "cases": [["f200-w4", {"Filter Freq": {"display": 200}, "Filter Width": 4}],
               ["f1000-w4", {"Filter Freq": {"display": 1000}, "Filter Width": 4}],
               ["f5000-w4", {"Filter Freq": {"display": 5000}, "Filter Width": 4}],
               ["f1000-w1", {"Filter Freq": {"display": 1000}, "Filter Width": 1}],
               ["f1000-w9", {"Filter Freq": {"display": 1000}, "Filter Width": 9}]]},

    {"name": "beatrepeat-mix-modes", "plan": "9", "probe": "gap2", "read": ["modulation", "dynamics", "static"],
     "priority": 2,
     "why": "what the output holds before, during and after the repeats in Mix, Ins and Gate (level, crossfades at the switch)",
     "question": "envelope of the steady tone and bursts in each Mix Type with Gate 4/16 at Interval 1 Bar",
     "base": dict(BASE, **{"Gate": 3, "Grid": GRID["1/8"]}),
     "cases": [["mix", {"Mix Type": {"item": "Mix"}}], ["ins", {"Mix Type": {"item": "Ins"}}],
               ["gate", {"Mix Type": {"item": "Gate"}}]]},

    {"name": "beatrepeat-variation", "plan": "5", "probe": "gap2", "read": ["impulse"], "priority": 3,
     "why": "snapshot of the Grid chosen under Variation in each mode and with No Triplets (one draw per bar, taps show the spacing)",
     "question": "tap spacing for Variation 5 and 10 (Trigger), Variation 10 with Auto and 1/16, and No Triplets on",
     "base": BASE,
     "cases": [["var-5", {"Variation": 5}], ["var-10", {"Variation": 10}],
               ["var-10-auto", {"Variation": 10, "Variation Type": {"item": "Auto"}}],
               ["var-10-sixteenth", {"Variation": 10, "Variation Type": {"item": "1/16"}}],
               ["var-10-no-triplets", {"Variation": 10, "Block Triplets": {"item": "On"}}]]},

    # ---- third set: Grid 1/6 replayed 375 ms slices when stored; the same value by a lane
    {"name": "beatrepeat-grid-lane", "plan": "2", "probe": "gap2", "read": ["impulse", "envelope"], "priority": 1,
     "why": "whether Grid 1/6 and 1/3 give triplet slices when set by an automation lane instead of the stored value",
     "question": "repeat spacing of the impulse for Grid 1/6 and 1/3 jumped in at beat 0.25 by a lane, against the stored values",
     "base": BASE,
     "cases": [["lane-1-6", {"Grid": {"auto": [[0, GRID["1/16"]], [0.25, GRID["1/6"]]]}}],
               ["lane-1-3", {"Grid": {"auto": [[0, GRID["1/16"]], [0.25, GRID["1/3"]]]}}],
               ["stored-1-6", {"Grid": GRID["1/6"]}]]},

    # The dump shows Grid's labels change between integers (1/6 first appears at 10.08, 1/3 at
    # 12.19), while the runs stored whole numbers. The same Grid by a lane gave the same slices
    # (beatrepeat-grid-lane), so the stored value is read as Live reads it; midpoints of the
    # labels' ranges show whether the triplet values exist at all.
    {"name": "beatrepeat-grid-midpoints", "plan": "2", "probe": "gap2", "read": ["envelope", "impulse"], "priority": 1,
     "why": "the slice length at the middle of each triplet label's range and at the integers either side of 1/6, to settle what the triplet Grids do",
     "question": "repeat spacing on the steady tone and impulse for Grid 2.6 (1/96), 4.7 (1/48), 6.6 (1/24), 8.7 (1/12), 9.6 (1/8), 10.5 (1/6), 12.6 (1/3), and 9.0, 11.0",
     "base": BASE,
     "cases": [[f"grid-{v}", {"Grid": v}] for v in (2.6, 4.7, 6.6, 8.7, 9.6, 10.5, 12.6, 9.0, 11.0)]},

    {"name": "beatrepeat-chance-quarters", "plan": "4", "probe": "gap2", "read": ["envelope"], "priority": 2,
     "why": "Chance statistics: with Interval 1/4 and Gate 1/8 every quarter note is a draw, about 40 per render over the probe's sounding segments (Mix Type Ins, so a trigger cuts the input)",
     "question": "which quarters repeat at Chance 25, 50 and 75 % (and 50 % on a second track with an unused setting changed, to see whether two devices draw alike)",
     "base": dict(BASE, **{"Interval": INTERVAL["1/4"], "Gate": 1, "Mix Type": {"item": "Ins"}}),
     "cases": [[f"chance-{c}", {"Chance": {"display": c}}] for c in (25, 50, 75)] +
              [["chance-50-b", {"Chance": {"display": 50}, "Filter Width": 2}]]},

    {"name": "beatrepeat-variation-quarters", "plan": "5", "probe": "gap2", "read": ["envelope", "impulse"], "priority": 2,
     "why": "Variation draws: Interval 1/4 gives about 40 triggers per render, so the drawn Grids can be counted per mode",
     "question": "slice lengths per trigger at Interval 1/4, Gate 1/4, Variation 5 in each Variation Type, and Variation 10 in Auto with No Triplets on",
     "base": dict(BASE, **{"Interval": INTERVAL["1/4"], "Gate": 3, "Variation": 5}),
     "cases": [[f"var5-{t.replace('/', '-').lower()}", {"Variation Type": {"item": t}}] for t in ("Trigger", "1/4", "1/8", "1/16", "Auto")] +
              [["var10-auto-notrip", {"Variation": 10, "Variation Type": {"item": "Auto"}, "Block Triplets": {"item": "On"}}]]},

    {"name": "beatrepeat-interactions", "plan": "10", "probe": "gap2", "read": ["envelope", "impulse"], "priority": 3,
     "why": "Gate longer than Interval, and Repeat (forced repetition) at Chance 0, switched on and off by a lane during the steady tone",
     "question": "Interval 1/4 with Gate 1/2; Chance 0 with Repeat on from beat 44 to beat 48 (22 to 24 s)",
     "base": BASE,
     "cases": [["gate-over-interval", {"Interval": INTERVAL["1/4"], "Gate": 7}],
               ["repeat-lane-chance0", {"Chance": {"display": 0},
                                        "Repeat": {"auto": [[0, {"item": "Off"}], [44, {"item": "On"}], [48, {"item": "Off"}]]}}]]},
]
