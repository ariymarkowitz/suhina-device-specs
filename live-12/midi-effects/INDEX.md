# Live 12 MIDI effects

One note per device of manual chapter 30. *Note* is `draft` until it has been checked against
Live, `dump checked` once its ranges, defaults, steps, tapers and `.als` names come from a
Live 12.4.6 parameter dump, and `partly measured` once runs in Live 12.4.6 have answered some of
its Measurement plan (facts tagged `[measured 12.4.6]`). Shared controls and behaviour (the
title bar, Scale Awareness, sync and transport, note-off handling, MPE) are in
[common.md](common.md).

| § | Device | Family | Note | Remarks |
|---|---|---|---|---|
| 30.1 | [Arpeggiator](30.01-arpeggiator.md) | note generation | partly measured | the dump confirms the Live 11 manual's 18 styles in order; Scale chooser is Chromatic plus 35 scales; Groove is a fixed Straight / Swing 8 / 16 / 32 list, not the Groove Pool; note orders still from the Live 11 manual |
| 30.2 | [CC Control](30.02-cc-control.md) | control | partly measured | Pitch Bend is −64 … 64 (recorded as −8192 … 8191); Custom A is CC 64; set values send nothing until changed; CC Types and names are stored state, not parameters; the probe reads its class_name as `0` |
| 30.3 | [Chord](30.03-chord.md) | note generation | partly measured | separate semitone and scale-degree Shifts; Strum ±400 ms on a quadratic taper; Send Per Note Events is on in a fresh device; manual and 12.0 release notes disagree on whether Learn also sets the velocities |
| 30.4 | [Note Length](30.04-note-length.md) | note transformation | partly measured | synced lengths only 0, 1/64 … 1/4; Trigger Source shows Off / On; Trigger Source Off is Note On; Note Off velocity = decayed note-on velocity blended with the release velocity (126^(−held/Decay)); Latch ends a gesture's notes when the next gesture triggers; Key Scale is not settled |
| 30.5 | [Pitch](30.05-pitch.md) | note transformation | partly measured | separate semitone and scale-degree Pitch and Step Width; Block tests Lowest/Range on the input, Fold (a wrap, period Range + 1) and Limit act after the transposition; out-of-range pitches are clamped |
| 30.6 | [Random](30.06-random.md) | note transformation | partly measured | loads with Chance 0 %; shifts are 1 … Choices times Interval (0 only in Alt, where it comes first); pitch clamped; scale mode snaps to the nearest scale note, ties down |
| 30.7 | [Scale](30.07-scale.md) | note transformation | partly measured | grid is 12 parameters Map 0 … 11, each −1 … 12: 12 columns × 13 rows, one square per column (settles the manuals' 12 × 12 / 13 × 13); 35 named scales plus User |
| 30.8 | [Velocity](30.08-velocity.md) | note transformation | partly measured | loads with Lowest 1, Out Low 1, Operation Both (resets to Velocity); Random tops at 64; Drive and Compand are power laws, exponent 1 / (1 + 3c) or 1 + 3|c|, Drive first; velocities leave as fractions |
