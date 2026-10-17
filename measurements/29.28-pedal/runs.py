# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Pedal behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.28-pedal.md > Measurement plan.

The base is Overdrive, Gain 0 %, Output 0 dB, EQ flat (Bass, Mid, Treble 0 %, Mid Freq Mid), Sub
off, Dry/Wet 100 %. The staircase (1 kHz) gives the transfer curve, THD and harmonics of each type; the
EQ is read from the sweep and the noise, with the unprocessed default case as the reference (the EQ
comes after the distortion, so the distortion of the sweep level is common to all cases).

Not measurable this way: plan 1's 20 Hz and 5 kHz tones (only 1 kHz is in the probe); plan 5
(Hi-Quality is a context-menu option, not a parameter); plan 6 (switching during the render needs
automation); the staircase has 3 dB steps instead of 10 dB."""

DEVICE = "Pedal"

BASE = {"Type": {"item": "Overdrive"}, "Drive": {"display": 0}, "Output": {"display": 0},
        "Bass": {"display": 0}, "Mid": {"display": 0}, "Treble": {"display": 0},
        "Mid Freq": {"item": "Mid"}, "Sub": {"item": "Off"}, "Dry/Wet": {"display": 100}}


def case(typ, gain):
    return [f"{typ[:4].lower()}-{gain}", {"Type": {"item": typ}, "Drive": {"display": gain}}]


RUNS = [
    {"name": "pedal-types", "plan": "1", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the three circuits' transfer curves, THD and odd/even harmonics at Gain 0, 50 and 100 % (Overdrive at 0 % is the default case)",
     "question": "staircase at 1 kHz for Overdrive, Distortion and Fuzz at Gain 0, 50 and 100 %, EQ flat",
     "base": BASE,
     "cases": [case("Overdrive", 50), case("Overdrive", 100), case("Distortion", 0), case("Distortion", 50),
               case("Distortion", 100), case("Fuzz", 0), case("Fuzz", 50), case("Fuzz", 100)]},

    {"name": "pedal-gain-taper", "plan": "2", "probe": "gap2", "read": ["static"], "priority": 1,
     "why": "the Gain control's law: small-signal gain and onset of distortion at Gain 25 and 75 % for each type",
     "question": "staircase at 1 kHz for each type at Gain 25 and 75 %, EQ flat (reads the low-level gain and the knee)",
     "base": BASE,
     "cases": [case(t, g) for t in ("Overdrive", "Distortion", "Fuzz") for g in (25, 75)]},

    {"name": "pedal-eq-mid", "plan": "3", "probe": "gap2", "read": ["response.sweep_db", "response.noise_db"], "priority": 2,
     "why": "the Mid band: centre at each Mid Freq position, width (narrow at low, wide at high), gain range and adaptive Q for boost and cut",
     "question": "Mid +100 % at Mid Freq Low, Mid and High; Mid +50 %; Mid -100 % and -50 % at Mid; Mid -100 % at Low",
     "base": BASE,
     "cases": [
         ["mid+100-low", {"Mid": {"display": 100}, "Mid Freq": {"item": "Low"}}],
         ["mid+100-mid", {"Mid": {"display": 100}}],
         ["mid+100-high", {"Mid": {"display": 100}, "Mid Freq": {"item": "High"}}],
         ["mid+50-mid", {"Mid": {"display": 50}}],
         ["mid-100-mid", {"Mid": {"display": -100}}],
         ["mid-50-mid", {"Mid": {"display": -50}}],
         ["mid-100-low", {"Mid": {"display": -100}, "Mid Freq": {"item": "Low"}}],
     ]},

    {"name": "pedal-eq-bass-treble", "plan": "3", "probe": "gap2", "read": ["response.sweep_db", "response.noise_db"], "priority": 2,
     "why": "the Bass peak (100 Hz), Treble shelf (3.3 kHz) and Sub shelf (250 Hz): gain range, Q and the Bass/Sub pairing",
     "question": "Bass +100, +50 and -100 %; Treble +100, +50 and -100 %; Sub on; Sub on with Bass -100 %",
     "base": BASE,
     "cases": [
         ["bass+100", {"Bass": {"display": 100}}],
         ["bass+50", {"Bass": {"display": 50}}],
         ["bass-100", {"Bass": {"display": -100}}],
         ["treble+100", {"Treble": {"display": 100}}],
         ["treble+50", {"Treble": {"display": 50}}],
         ["treble-100", {"Treble": {"display": -100}}],
         ["sub", {"Sub": {"item": "On"}}],
         ["sub-bass-100", {"Sub": {"item": "On"}, "Bass": {"display": -100}}],
     ]},

    {"name": "pedal-output-mix", "plan": "4", "probe": "gap2", "read": ["static", "impulse"], "priority": 3,
     "why": "Output in real dB, the Dry/Wet law, and whether the dry path is aligned with the wet one",
     "question": "Output +12 and -12 dB; Dry/Wet 0 and 50 % at Distortion, Gain 50 %",
     "base": BASE | {"Type": {"item": "Distortion"}, "Drive": {"display": 50}},
     "cases": [
         ["out+12", {"Output": {"display": 12}}],
         ["out-12", {"Output": {"display": -12}}],
         ["dw-0", {"Dry/Wet": {"display": 0}}],
         ["dw-50", {"Dry/Wet": {"display": 50}}],
     ]},
]
