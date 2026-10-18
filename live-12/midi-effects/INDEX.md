# Live 12 MIDI effects

One note per device of manual chapter 30. *Note* is `draft` until it has been checked against
Live, `dump checked` once its ranges, defaults, steps, tapers and `.als` names come from a
Live 12.4.6 parameter dump, and `partly measured` once runs in Live 12.4.6 have answered some of
its Measurement plan (facts tagged `[measured 12.4.6]`). Shared controls and behaviour (the
title bar, Scale Awareness, sync and transport, note-off handling, MPE) are in
[common.md](common.md).

| § | Device | Family | Note | Remarks |
|---|---|---|---|---|
| 30.1 | [Arpeggiator](30.01-arpeggiator.md) | note generation | dump checked | the dump confirms the Live 11 manual's 18 styles in order; Scale chooser is Chromatic plus 35 scales; Groove is a fixed Straight / Swing 8 / 16 / 32 list, not the Groove Pool; note orders still from the Live 11 manual |
| 30.2 | [CC Control](30.02-cc-control.md) | control | dump checked | Pitch Bend is −64 … 64; CC Types and names are stored state, not parameters; the probe reads its class_name as `0` |
| 30.3 | [Chord](30.03-chord.md) | note generation | dump checked | separate semitone and scale-degree Shifts; Strum ±400 ms on a quadratic taper; Send Per Note Events is on in a fresh device; manual and 12.0 release notes disagree on whether Learn also sets the velocities |
| 30.4 | [Note Length](30.04-note-length.md) | note transformation | dump checked | synced lengths only 0, 1/64 … 1/4; Trigger Source shows Off / On; Latch rules in 12.0 are ambiguous |
| 30.5 | [Pitch](30.05-pitch.md) | note transformation | dump checked | separate semitone and scale-degree Pitch and Step Width; Live 11 manual tests Lowest/Range before transposing; the Live 12 manual drops that |
| 30.6 | [Random](30.06-random.md) | note transformation | dump checked | loads with Chance 0 %; manual examples disagree on whether a shift of 0 is among the choices |
| 30.7 | [Scale](30.07-scale.md) | note transformation | dump checked | grid is 12 parameters Map 0 … 11, each −1 … 12: 12 columns × 13 rows, one square per column (settles the manuals' 12 × 12 / 13 × 13); 35 named scales plus User |
| 30.8 | [Velocity](30.08-velocity.md) | note transformation | dump checked | loads with Lowest 1, Out Low 1, Operation Both (resets to Velocity); Random tops at 64; Drive and Compand (−1 … 1) curves unknown |
