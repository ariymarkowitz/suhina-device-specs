# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Spectrum behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.38-spectrum.md › Measurement plan.

Spectrum is an analyser; its only API parameter is Device On, and what it measures is a display that
no render captures: Block, Channel, Refresh, Avg, Graph, Max, Scale X and Range are plain values
(not settable here) and the plan's level, window, refresh, averaging and axis questions (plan 2 to 7)
are all about that display. The audio path is the one thing a render shows: the device should be
transparent. The single run below is that null test (bypass against the loaded state: bit-exact? any
delay?). It is the cheapest possible run and the lead may well leave it out.
"""

DEVICE = "Spectrum"

RUNS = [
    {"name": "spectrum-transparency", "plan": "8", "probe": "gap2", "read": ["impulse", "response", "static"], "priority": 3,
     "why": "the audio is unchanged and undelayed (null test of the render against the bypass)",
     "question": "is the render with the device on identical to the bypass render, sample for sample, in all probe segments?",
     "base": {},
     "cases": [["on", {"Device On": 1}]]},
]
