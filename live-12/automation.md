# Automation playback (Live 12.4.6)

How Live plays an arrangement automation lane: what a segment between two points moves along,
the shape of a bent segment, the volume fader's taper and how a jump is smoothed. It holds for
every parameter measured so far (four, on three devices and the mixer), so it is written once
here; a device's note points here for the part that is its own (a taper, a smoothing time).

Everything below is `[measured 12.4.6]` unless tagged otherwise: seven sets automating one
parameter each on a track playing Operator's sine (261.6 Hz), rendered and read back by
`measurements/automation/analyse.py`. The runs, the sets and how to make the renders again are in
[`measurements/automation/README.md`](../measurements/automation/README.md).

## Summary

- A segment moves **evenly along the parameter's own position**: the travel of its knob or
  fader (0 to 1), not its stored value and not dB. What is drawn straight on the lane is what is
  heard.
- A bent segment is a **cubic Bezier** in (share of the time, share of the way in position),
  whose two control points mirror each other: one handle sets the bend.
- **Track volume** and **Operator's Volume** share one fader taper: even in dB at 40 dB per
  travel from -18 dB to +6 dB, 0 dB at 0.85 of the travel, falling faster below.
- **A jump on a gain parameter is smoothed** by a fixed-time S-shaped ramp, even in position and
  centred on the jump: 4.3 to 4.4 ms for Utility's Gain and the track volume, about 8.7 ms for
  Operator's Volume. A pitch parameter (Operator's Fine) is not smoothed.

## Segments move evenly in position

The automation stores each point's value in the parameter's stored unit (linear gain for the
track volume, Utility's Gain and Operator's Volume; Fine's own number for Operator's Fine)
[als 12.4.6]. Played back, a segment does not interpolate that stored value. It interpolates
the parameter's **position** p, 0 to 1 over the travel of its control, and converts back:

    p(t) = p(a) + (p(b) - p(a)) * y(x),   x = share of the segment's time, y = its curve (below)
    value(t) = the parameter's value at position p(t)

Error of each reading, from every segment of every run (renders against prediction, the
reference level fitted, 20 ms left out around each point):

| Run | Parameter | Even in position | Even in dB | Even in the stored value |
|---|---|---|---|---|
| utility-gain-curves | Utility Gain | 0.03 dB rms | 5.7 dB rms | 5.8 dB rms |
| track-volume | track Volume | 0.03 dB rms (0.29 max) | 4.6 dB rms | 5.4 dB rms |
| operator-volume-88k | Operator Volume | 0.02 dB rms (0.15 max) | 3.2 dB rms | 3.7 dB rms |
| operator-fine | Operator Fine | 1.5 cents rms | 14.7 cents rms (even in pitch) | |

For Utility's Gain the position is its knob's taper (the Utility note, Controls); for the two
volumes, the fader taper below; Fine's knob is linear in its own number, so Fine moves evenly in
Fine (ratio mode: frequency = base * (1 + Fine/1000)), not evenly in pitch. The largest single
errors sit where a segment ends steeply (the 2 ms level blocks average a fast change) and in the
20 ms before a 62 dB jump, where the level detector smears the jump.

## The curve family

A bent segment's point carries `CurveControl1X/Y` and `CurveControl2X/Y` in the set; a straight
segment has none [als 12.4.6]. They are the inner control points of a cubic Bezier from (0, 0) to
(1, 1), in (share of the time, share of the way in position), and the prediction above uses them
as such: all six bent segments of the track volume run and the four of each Utility run fit to
0.03 dB rms or better.

Every curve seen has **mirrored control points**: the second is (1 - y1, 1 - x1), the first
reflected across the line x + y = 1. The bend is one handle. Seen values (x1, y1): (1, 0) and
(0, 1) at the two extremes; (0.109, 0.672), (0.152, 0.543), (0.156, 0.531), (0.172, 0.484),
(0.199, 0.402) on one side; (0.367, 0.211), (0.473, 0.176), (0.484, 0.172), (0.543, 0.152) on
the other. They lie on two lines that meet at (1/4, 1/4):

- **Fast first** (the value moves early and settles): y1 = 1 - 3 x1, for x1 from 1/4 to 0.
- **Slow first** (the value waits and moves late): x1 = 1 - 3 y1, for y1 from 1/4 to 0.

(1/4, 1/4) with its mirror (3/4, 3/4) is a straight line. Whether Live's drag moves the handle
evenly along these lines is not known [measure]; only the family is.

The same stored controls give the same shape in (time, share of the way) whichever way the value
goes: with (1, 0, 1, 0), a falling segment holds high and drops late (utility-gain-curves, beats 6
to 10) and a rising one holds low and rises late (beats 10 to 18).

## The volume fader's taper

From the track volume run's straight segment from the lane's bottom (-70 dB stored, gain
0.000316, the least the lane stores) to its top (+6 dB, gain 1.995) over beats 3 to 6, where the
share of the time is the position; the table is `measurements/automation/live/fader-taper.csv`.
That table predicts every other segment of the run (0.03 dB rms) and every segment of
Operator's Volume at 88.2 kHz (0.02 dB rms), so the two share it.

| Position | 0.02 | 0.05 | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.70 | 0.85 | 1.00 |
|---|---|---|---|---|---|---|---|---|---|---|
| dB | -63.4 | -57.2 | -48.6 | -34.4 | -24.2 | -18.0 | -14.0 | -6.0 | 0.0 | +6.0 |

A formula that fits it [measured 12.4.6, fitted]:

- **0.4 to 1:** dB = 40 p - 34 (0 dB at 0.85, +6 dB at the top), within 0.002 dB.
- **Below 0.4:** dB = 40 p - 34 - 207 (0.4 - p)^2: 0.1 dB rms, within 0.25 dB above p = 0.05;
  it reaches -67 dB at the bottom, where the measured level falls to -70 dB over the last 1 % of
  the travel. The bottom of the travel is silence in the mixer [inferred].

## Smoothing of jumps

A jump (two points at one beat) was fitted on the raw samples with a ramp from the level before
to the level after: its length L and start free, its shape one of smootherstep (6u^5 - 15u^4 +
10u^3), a raised cosine, smoothstep (3u^2 - 2u^3) or a straight line, and evenly in position, in
dB or in gain. Best fits (residual lowest; the centre is in samples from the beat):

| Run | Jump | Rate | Shape, space | Length | Centre |
|---|---|---|---|---|---|
| utility-gain-jump13 | -9.4 to +3.7 dB | 44.1 kHz | smootherstep, position (= dB above -17.5 dB) | 190 samples, 4.31 ms | 0 |
| utility-gain-jump62 | -54.7 to +7.8 dB | 44.1 kHz | smootherstep, position | 196 samples, 4.44 ms | -1 |
| utility-gain-jump62-88k | -54.7 to +7.8 dB | 88.2 kHz | smootherstep, position | 391 samples, 4.43 ms | -1.5 |
| track-volume | -13.0 to -2.4 dB | 44.1 kHz | smootherstep, position (= dB above -18 dB) | 191 samples, 4.33 ms | -0.5 |
| operator-volume-88k | -50.3 to -7.1 dB | 88.2 kHz | smootherstep, position | 764 samples, 8.66 ms | +2 |

- **A fixed time, not a fixed number of samples:** the same 62 dB jump takes 196 samples at 44.1
  kHz and 391 at 88.2 kHz, 4.4 ms both times; 200 samples forced at 88.2 kHz fits 16 times worse.
- **Evenly in position:** for the 62 dB jump, a ramp even in dB fits as well only if it is 5.6 ms
  long at 44.1 kHz and centred 0.5 ms early, and the 13 dB jump (where dB and position are the
  same) says 4.3 ms on the beat; a ramp even in position is 4.3 to 4.4 ms and on the beat for
  both. Even in gain fits four to five times worse.
- **Centred on the jump:** the ramp starts half its length before the point, so it reads the
  automation ahead of time [inferred]; it is not a filter that only starts at the point (a one-pole
  ramp fits several times worse).
- **The shape** is an S that starts and ends without a corner; smootherstep fits best of the four,
  but another S of that kind would fit nearly as well [inferred].
- **Each parameter has its own time:** Operator's Volume takes about twice as long as Utility's
  Gain and the track volume.
- **Not smoothed:** Operator's Fine jumps from one frequency to the other within 0.5 ms (the
  limit of the frequency reading), up and down.

A straight segment shows no steps: Utility's Gain moving at 10.8 dB/s is within 0.03 dB of a
straight line in dB over a second (utility-gain-curves, beats 4 to 6).

## Open

- How Alt-drag (Option on macOS) moves the curve handle with the mouse [measure].
- The smoothing of a mute, and of a gain parameter's continuous motion faster than its ramp time
  [measure].
- Other parameter kinds: a frequency knob (logarithmic), a choice, a toggle [measure].
- Whether a lane interpolates in position for every device, plug-ins included [measure].
