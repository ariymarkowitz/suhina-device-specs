# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tuner behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.39-tuner.md › Measurement plan.

The Tuner reads pitch and shows it on a display; its only API parameter is Device On, the Reference
(`TuningFreq`) is a plain value with no API parameter, and the readout, ball, strobe, histogram and
colours are not in the audio. Plan steps 2 to 9 (accuracy, limits, response time, strobe, colours,
hold, spellings, tuning systems) therefore cannot be measured from a render. The audio path is the one
thing a render shows: the device should be transparent. The single run below is that null test
(bypass against the loaded state). It is the cheapest possible run and the lead may well leave it out.
"""

DEVICE = "Tuner"

RUNS = [
    {"name": "tuner-transparency", "plan": "-", "probe": "gap2", "read": ["impulse", "response", "static"], "priority": 3,
     "why": "the audio is unchanged and undelayed (null test of the render against the bypass)",
     "question": "is the render with the device on identical to the bypass render, sample for sample, in all probe segments?",
     "base": {},
     "cases": [["on", {"Device On": 1}]]},
]
