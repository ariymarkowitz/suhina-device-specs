# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""External Audio Effect behaviour runs for tools/harness/measure.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.18-external-audio-effect.md › Measurement plan.

With no audio interface output or input chosen (the loaded state) the device has no hardware to
send to or return from, so only its own gain stages and the mix can be seen: what the wet path
is when nothing is routed (silence, or the dry), the Dry/Wet law, and whether either Gain acts on
the dry signal. The run below does that.

Left out (cannot be measured this way): everything that needs a loopback or a hardware effect:
timing against Hardware Latency, ms against samples, the unit button, Delay Compensation (plan 2, 7);
the peak indicators (plan 5, display only); the stereo-to-mono send sum (4); Invert, which is not an
API parameter and acts on the returned signal only (6). The Hardware Latency is not a parameter.
Which of the two Gain knobs is Output Gain and Input Gain (plan 1) cannot be told without routing,
but the two cases below show whether either does anything with nothing routed.
"""

DEVICE = "External Audio Effect"

RUNS = [
    {"name": "external-audio-effect-unrouted-mix", "plan": "3, 4", "probe": "gap2", "read": ["static", "silence", "impulse"], "priority": 3,
     "why": "what the unrouted device outputs at Dry/Wet 100 % (silence?) and the Dry/Wet law, and that neither Gain touches the dry signal",
     "question": "staircase gain and impulse delay for Dry/Wet 0, 25, 50, 75 % (default 100 %), and at 50 % Output Gain +12 dB, Input Gain +12 dB, Input Gain -inf",
     "base": {},
     "cases": [[f"dw-{d}", {"Dry/Wet": {"display": d}}] for d in (0, 25, 50, 75)]
     + [["dw50-outgain+12", {"Dry/Wet": {"display": 50}, "Output Gain": {"display": 12}}],
        ["dw50-ingain+12", {"Dry/Wet": {"display": 50}, "Input Gain": {"display": 12}}],
        ["dw50-ingain--inf", {"Dry/Wet": {"display": 50}, "Input Gain": {"norm": 0.0}}]]},

    # ---- third set: the Hardware Latency is a stored value
    # (LatencyValue/Value, in ms unless IsValueSampleBased), so its effect on the unrouted
    # device's dry path can be rendered
    {"name": "external-audio-effect-latency", "plan": "2, 7", "probe": "gap2", "read": ["impulse"], "priority": 3,
     "why": "whether the Hardware Latency setting delays the dry path or shifts the track, and the unit switch",
     "question": "impulse through the unrouted device at Dry/Wet 0 and 50 % with Hardware Latency 10 ms, and 441 samples with the unit in samples",
     "base": {"Dry/Wet": {"display": 50}},
     "cases": [["lat10ms-dry0", {"Dry/Wet": {"display": 0}, "@LatencyValue/Value": 10}],
               ["lat10ms-dry50", {"@LatencyValue/Value": 10}],
               ["lat441smp-dry50", {"@LatencyValue/Value": 441, "@LatencyValue/IsValueSampleBased": True}]]},
]
