# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Overdrive behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.27-overdrive.md > Measurement plan.

The base is the wet path only (Dry/Wet 100 %) with the band at 1 kHz, width 6.5 (the default), Drive
50 %, Tone 50 %, Dynamics 100 % (the least internal compression). The probe's staircase (1 kHz) gives
the transfer curve with its THD and harmonics, the sweep and noise give the band and Tone shapes.

Not measurable this way: the plan's 200 Hz sine (the probe has only a 1 kHz tone, so a lower
frequency can only be reached through the band filter and Tone); the 6 dB staircase (it is 3 dB);
whether a Hi-Quality option exists (not a parameter, so no case)."""

DEVICE = "Overdrive"

BASE = {"Filter Freq": {"display": 1000}, "Filter Width": 6.5, "Drive": {"display": 50},
        "Tone": {"display": 50}, "Preserve Dynamics": {"display": 100}, "Dry/Wet": {"display": 100}}

RUNS = [
    {"name": "overdrive-drive", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the distortion curve: output level, THD and the odd/even harmonics against Drive (0 % still distorts), and the level change with Dynamics at 0 %",
     "question": "staircase at 1 kHz for Drive 0, 25, 75 and 100 % (50 % is the default case) at Dynamics 100 %, and Drive 50 and 100 % at Dynamics 0 %",
     "base": BASE,
     "cases": [[f"drive-{v}", {"Drive": {"display": v}}] for v in (0, 25, 75, 100)] + [
         ["drive-50-dyn-0", {"Preserve Dynamics": {"display": 0}}],
         ["drive-100-dyn-0", {"Drive": {"display": 100}, "Preserve Dynamics": {"display": 0}}],
     ]},

    {"name": "overdrive-dynamics", "plan": "3", "probe": "gap2", "read": ["dynamics", "static"], "priority": 1,
     "why": "the internal compression and make-up of Dynamics: level difference between the -30 and -6 dBFS bursts, and its attack and release",
     "question": "bursts at Drive 100 % with Dynamics 0, 50 and 100 % (100 % is the default case)",
     "base": BASE | {"Drive": {"display": 100}},
     "cases": [[f"dyn-{v}", {"Preserve Dynamics": {"display": v}}] for v in (0, 50)]},

    {"name": "overdrive-band", "plan": "1", "probe": "gap2", "read": ["response.sweep_db", "response.noise_db"], "priority": 1,
     "why": "the pre-distortion band: centre, slopes, and what the Bandwidth number means (octaves or Q), against Frequency and Bandwidth",
     "question": "Drive 0 %, Tone 50 %: Frequency 1 kHz at Bandwidth 0.5, 4.75 and 9; Frequency 100 Hz and 8 kHz at Bandwidth 4.75",
     "base": BASE | {"Drive": {"display": 0}},
     "cases": [
         ["f1k-w0.5", {"Filter Width": 0.5}],
         ["f1k-w4.75", {"Filter Width": 4.75}],
         ["f1k-w9", {"Filter Width": 9}],
         ["f100-w4.75", {"Filter Freq": {"display": 100}, "Filter Width": 4.75}],
         ["f8k-w4.75", {"Filter Freq": {"display": 8000}, "Filter Width": 4.75}],
     ]},

    {"name": "overdrive-tone", "plan": "4", "probe": "gap2", "read": ["response.sweep_db", "response.noise_db"], "priority": 1,
     "why": "the Tone filter: type (tilt, shelf or pass), corner and slope; and whether it still acts at Dry/Wet 0 %",
     "question": "Drive 0 %, widest band: Tone 0, 25, 75 and 100 % (50 % is the default case); Tone 0 and 100 % at Dry/Wet 0 %",
     "base": BASE | {"Drive": {"display": 0}, "Filter Width": 9},
     "cases": [[f"tone-{v}", {"Tone": {"display": v}}] for v in (0, 25, 75, 100)] + [
         ["dw0-tone-0", {"Tone": {"display": 0}, "Dry/Wet": {"display": 0}}],
         ["dw0-tone-100", {"Tone": {"display": 100}, "Dry/Wet": {"display": 0}}],
     ]},

    {"name": "overdrive-drywet", "plan": "5", "probe": "gap2", "read": ["impulse", "static"], "priority": 2,
     "why": "the Dry/Wet law (linear?) and whether the dry path is delay-compensated against the wet one (no comb)",
     "question": "Dry/Wet 0, 25 and 75 % at Drive 75 % (100 % is the wet-only base)",
     "base": BASE | {"Drive": {"display": 75}},
     "cases": [[f"dw-{v}", {"Dry/Wet": {"display": v}}] for v in (0, 25, 75)]},

    # ---- third set: the extended probe's 100 Hz staircase, 1 kHz ramp and
    # 3 kHz sine stand in for the plan's 200 Hz and 2 kHz curves
    {"name": "overdrive-curves-100hz", "plan": "2", "probe": "ext", "read": ["ext: stair100, ramp, tone3k"], "priority": 2,
     "why": "the drive curve at a low and a high frequency (the band-pass in front shapes what the shaper sees)",
     "question": "100 Hz staircase, 1 kHz ramp and 3 kHz sine at Drive 0, 25, 50, 75, 100 % with Dynamics 100 %, and Drive 100 % at Dynamics 0 %",
     "base": BASE,
     "cases": [[f"drive-{d}", {"Drive": {"display": d}}] for d in (0, 25, 75, 100)] +
              [["drive-100-dyn0", {"Drive": {"display": 100}, "Preserve Dynamics": {"display": 0}}]]},
]
