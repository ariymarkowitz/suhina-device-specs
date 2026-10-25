# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Looper behaviour runs for tools/harness/batch.py (see its docstring for the format).
Plan steps refer to live-12/audio-effects/29.25-looper.md › Measurement plan.

Almost nothing of the Looper is measurable in a static render: its behaviour is a state machine
driven by button presses during playback (Record, Play, Overdub, Stop, Clear, Undo, x2, /2,
the octave buttons), and none of those can be pressed during the export. The one thing a static
render can show is what the `State` and `Monitor` parameters do from the first sample, so the
single run below samples that. Tempo Control, Song Control and Quantization are set so that the
device cannot move the set's tempo or wait for a bar line.

A State lane (parameter lanes in a run's `auto`, `{"auto": [[beat, spec], ...]}`) does press the buttons
during the export: the third set recorded and overdubbed with one, and the fifth set read Feedback, the
fades at the edges, Speed and Reverse from a noise take and a tone take.

Left out (cannot be measured this way): maximum length (plan 3), Undo semantics (6), tempo guess (7),
Quantization offsets (8), Song/Tempo Control (10), fixed Record Length (11, not a parameter), Record
Length's list (1).
"""

DEVICE = "Looper"

# No tempo or transport changes, act at once.
BASE = {"Tempo Control": {"item": "None"}, "Song Control": {"item": "None"},
        "Quantization": {"item": "None"}}


def case(cid, state, monitor):
    return [cid, {"State": {"item": state}, "Monitor": {"item": monitor}}]


RUNS = [
    {"name": "looper-monitor-states", "plan": "9", "probe": "gap2", "read": ["silence", "static", "raw render (is anything but the input heard?)"], "priority": 3,
     "why": "when the input is audible in each State for each Input -> Output choice, and whether a State set from the start records and plays back anything",
     "question": "output level with the state fixed from the first sample: Stop with Never, Rec/OVR, Rec/OVR/Stop; Record with Never and Rec/OVR; Play with Rec/OVR and Rec/OVR/Stop; Overdub with Rec/OVR/Stop (default: Stop, Always)",
     "base": BASE,
     "cases": [case("stop-never", "Stop", "Never"), case("stop-recovr", "Stop", "Rec/OVR"),
               case("stop-recovrstop", "Stop", "Rec/OVR/Stop"), case("record-never", "Record", "Never"),
               case("record-recovr", "Record", "Rec/OVR"), case("play-recovr", "Play", "Rec/OVR"),
               case("play-recovrstop", "Play", "Rec/OVR/Stop"), case("overdub-recovrstop", "Overdub", "Rec/OVR/Stop")]},

    # ---- third set: the State is played by an automation lane, so the device acts during the
    # render (beat 1 = 0.5 s of the probe; the impulse is at beat 1)
    {"name": "looper-state-lane", "plan": "4, 9, 12", "probe": "gap2", "read": ["impulse", "raw render"], "priority": 1,
     "why": "whether a State lane makes the Looper record and play back: recording beats 0.5 to 4 holds the impulse, so playback repeats it every 1.75 s",
     "question": "the render with State Record at beat 0.5 and Play at beat 4; then Record 0.5, Overdub 4, Play 8; Monitor Always",
     "base": BASE,
     "cases": [["rec-play", {"State": {"auto": [[0, {"item": "Stop"}], [0.5, {"item": "Record"}], [4, {"item": "Play"}]]}}],
               ["rec-overdub-play", {"State": {"auto": [[0, {"item": "Stop"}], [0.5, {"item": "Record"}],
                                                        [4, {"item": "Overdub"}], [8, {"item": "Play"}]]}}]]},

    # ---- fifth set: a noise take. The probe's noise is at 30.75 to 34.75 s (beats 61.5 to 69.5); a
    # 1 s loop (two beats) is recorded from beat 61.75, so the noise of the next two seconds is
    # overdubbed in two passes, and the loop is read back in the silence at the end of the probe.
    {"name": "looper-feedback-noise", "plan": "4, 9, 12", "probe": "gap2", "read": ["raw render in the silence (loop against the noise)"], "priority": 1,
     "why": "the third set's Overdub pass left the first take at 0.42 and the Record to Play playback at 0.95: noise passes at several Feedback values give the factor on the take, on each pass, and where it changes with the position in the loop",
     "question": "Record from beat 61.75 to 63.75 (a 1 s loop of the noise), Overdub to 67.75 (two more passes), Play after: the loop read back in the silence is regressed on the three stretches of the noise, for Feedback 100, 75, 50, 25 and 0 % with Monitor Never; Feedback 100 % with Monitor Always; Record to Play without an Overdub pass at Never and Always; Feedback 100 % lane to 25 % at beat 64.5 (mid first pass); an Overdub pass that starts and ends away from the loop boundary",
     "base": dict(BASE, **{"Monitor": {"item": "Never"}, "Feedback": {"display": 100}}),
     "cases": [[f"fb{fb}", {"Feedback": {"display": fb},
                           "State": {"auto": [[0, {"item": "Stop"}], [61.75, {"item": "Record"}], [63.75, {"item": "Overdub"}], [67.75, {"item": "Play"}]]}}]
               for fb in (100, 75, 50, 25, 0)] +
              [["fb100-always", {"Monitor": {"item": "Always"},
                                 "State": {"auto": [[0, {"item": "Stop"}], [61.75, {"item": "Record"}], [63.75, {"item": "Overdub"}], [67.75, {"item": "Play"}]]}}],
               ["rec-play-never", {"State": {"auto": [[0, {"item": "Stop"}], [61.75, {"item": "Record"}], [63.75, {"item": "Play"}]]}}],
               ["rec-play-always", {"Monitor": {"item": "Always"},
                                   "State": {"auto": [[0, {"item": "Stop"}], [61.75, {"item": "Record"}], [63.75, {"item": "Play"}]]}}],
               ["fb-lane-mid-pass", {"Feedback": {"auto": [[0, {"display": 100}], [64.5, {"display": 100}], [64.5, {"display": 25}]]},
                                     "State": {"auto": [[0, {"item": "Stop"}], [61.75, {"item": "Record"}], [63.75, {"item": "Overdub"}], [67.75, {"item": "Play"}]]}}],
               ["od-edges", {"State": {"auto": [[0, {"item": "Stop"}], [61.75, {"item": "Record"}], [63.75, {"item": "Play"}],
                                                [64.25, {"item": "Overdub"}], [66.25, {"item": "Play"}]]}}]]},

    # the steady 1 kHz tone is at 20.75 to 28.75 s (beats 41.5 to 57.5), the sweep at 2.5 to 6.5 s
    # (beats 5 to 13): a 1 s loop (beats 42 to 44) of the tone read back at each Speed, and the sweep
    # recorded from beat 5.5 for 3 s (to beat 11.5) read forward and with Reverse
    {"name": "looper-speed-reverse", "plan": "2, 5", "probe": "gap2", "read": ["raw render (pitch of the loop; direction of the sweep)"], "priority": 3,
     "why": "the Speed knob's unit (semitones is inferred) and Reverse's direction, which need a recorded loop and so a lane",
     "question": "the 1 kHz tone recorded for 1 s (beat 42 to 44) and played at Speed 0, +12, -12, +7, +24 and -24; then the sweep recorded for 3 s (beat 5.5 to 11.5) and played at Speed 0 with Reverse off and on",
     "base": dict(BASE, **{"Monitor": {"item": "Never"}, "Feedback": {"display": 100}}),
     "cases": [[f"speed{sp:+d}".replace("+", "p").replace("-", "m"),
                {"Speed": sp, "State": {"auto": [[0, {"item": "Stop"}], [42, {"item": "Record"}], [44, {"item": "Play"}]]}}]
               for sp in (0, 12, -12, 7, 24, -24)] +
              [["sweep-fwd", {"State": {"auto": [[0, {"item": "Stop"}], [5.5, {"item": "Record"}], [11.5, {"item": "Play"}]]}}],
               ["sweep-reverse", {"Reverse": {"item": "On"},
                                  "State": {"auto": [[0, {"item": "Stop"}], [5.5, {"item": "Record"}], [11.5, {"item": "Play"}]]}}]]},
]
