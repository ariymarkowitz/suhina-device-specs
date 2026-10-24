# Automation playback and curve editing (Live 12.4.6)

How Live plays an arrangement automation lane: what a segment between two points moves along,
the shape of a bent segment, the volume fader's taper and how a jump is smoothed. It holds for
every parameter measured so far (four, on three devices and the mixer), so it is written once
here; a device's note points here for the part that is its own (a taper, a smoothing time). It
also says how Live's editor splits a bent segment and how dragging a curve reshapes it.

Everything below is `[measured 12.4.6]` unless tagged otherwise: ten sets automating one
parameter each on a track playing Operator's sine (261.6 Hz), rendered and read back by
`measurements/automation/analyse.py`; the split and dragged curves are read from three of those
sets by `measurements/automation/curve_drag.py`. The runs, the sets and how to make the renders
again are in [`measurements/automation/README.md`](../measurements/automation/README.md).

## Summary

- A segment moves **evenly along the parameter's own position**: the travel of its knob or
  fader (0 to 1), not its stored value and not dB. What is drawn straight on the lane is what is
  heard.
- A bent segment is a **cubic Bezier** in (share of the time, share of the way in position),
  with its two control points anywhere in the unit box. Bending a straight segment gives Live's
  own family, whose two points mirror each other (one handle sets the bend); splitting and
  dragging give other pairs.
- **Splitting** a bent segment cuts its Bezier exactly where the new point goes (de Casteljau),
  so the sound does not change.
- **Dragging** a curve moves each control point along a fixed path of its own, in steps of 1/64:
  both the same way when they are on one side of the diagonal, opposite ways when they are on
  opposite sides.
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
| utility-gain-splits | Utility Gain | 0.03 dB rms (1.3 max) | 0.03 dB rms | 0.86 dB rms |
| curve-drag | Utility Gain | 0.02 dB rms (0.55 max) | 0.02 dB rms | 0.75 dB rms |
| curve-drag-lopsided | Utility Gain | 0.03 dB rms (0.94 max) | 0.03 dB rms | 0.75 dB rms |

The three curve runs stay between 0 and +14.4 dB, where Utility's knob is even in dB, so there
the two columns agree; they test the curves, not the taper. The 1.3 dB maximum is the steep
segment under Smoothing of jumps › Fast curves.

For Utility's Gain the position is its knob's taper (the Utility note, Controls); for the two
volumes, the fader taper below; Fine's knob is linear in its own number, so Fine moves evenly in
Fine (ratio mode: frequency = base * (1 + Fine/1000)), not evenly in pitch. The largest single
errors sit where a segment ends steeply (the 2 ms level blocks average a fast change) and in the
20 ms before a 62 dB jump, where the level detector smears the jump.

## Curve shapes

A bent segment's point carries `CurveControl1X/Y` and `CurveControl2X/Y` in the set; a straight
segment has none [als 12.4.6]. They are the inner control points of a cubic Bezier from (0, 0) to
(1, 1), in (share of the time, share of the way in position), and the prediction above uses them
as such: all six bent segments of the track volume run, the four of each Utility run and every
bent segment of the three curve runs (S curves, crossed and lopsided control points, handles on
the edges of the box) fit to 0.03 dB rms or better, but for one steep segment (Smoothing of
jumps › Fast curves).

**Any two control points in the unit box.** The two points are independent: splitting a segment
and dragging other shapes give pairs that are not mirrored, with the second left of the first, or
one point on the top edge and one on the bottom [als 12.4.6]. Every point seen lies in the square
0 to 1 by 0 to 1, and Live's editor keeps them there (Dragging a curve › Ends). The square is
enough for playback [inferred]: with x1 and x2 in it, the time share x(t) never falls (its slope
3 ((1 - t)^2 x1 + 2 t (1 - t) (x2 - x1) + t^2 (1 - x2)) is least, 3 (1 - 2 t)^2, at x1 = 1,
x2 = 0), so the curve is a function of time; with y1 and y2 in it, the curve stays between its
two points.

**Live's own family.** Bending a straight segment gives **mirrored control points**: the second
is (1 - y1, 1 - x1), the first reflected across the line x + y = 1, so the bend is one handle.
Seen values (x1, y1): (1, 0) and (0, 1) at the two extremes; (0.109, 0.672), (0.152, 0.543),
(0.156, 0.531), (0.172, 0.484), (0.199, 0.402) on one side; (0.367, 0.211), (0.473, 0.176),
(0.484, 0.172), (0.543, 0.152) on the other. They lie on two lines that meet at (1/4, 1/4):

- **Fast first** (the value moves early and settles): y1 = 1 - 3 x1, for x1 from 1/4 to 0.
- **Slow first** (the value waits and moves late): x1 = 1 - 3 y1, for y1 from 1/4 to 0.

(1/4, 1/4) with its mirror (3/4, 3/4) is a straight line. A drag moves along these lines in steps
of 1/256 of x1 (Dragging a curve: the family is the paths with p = 1/4 and 3/4).

The same stored controls give the same shape in (time, share of the way) whichever way the value
goes: with (1, 0, 1, 0), a falling segment holds high and drops late (utility-gain-curves, beats 6
to 10) and a rising one holds low and rises late (beats 10 to 18). Dragging behaves the same on a
rising and a falling segment too (curve-drag, bars 2 and 13, 7 and 14 of each copy).

## Splitting a segment

Placing a point on a bent segment keeps its shape exactly (utility-gain-splits: bars 1 to 4 are
eight bent segments of Live's family, bars 5 to 8 the same segments with a point placed on each).
For a point placed at share x of the segment's time:

1. Live finds the Bezier's parameter t where the curve's time share is x.
2. The new point's value is the parameter's value at the curve's position there, stored in the
   parameter's unit as any point is.
3. Each half gets the de Casteljau subdivision at t, scaled to its own box. With the control
   points P0 = (0, 0), P1, P2, P3 = (1, 1):

       Q = P0 + (P1 - P0) t,  R = P1 + (P2 - P1) t,  S = P2 + (P3 - P2) t
       U = Q + (R - Q) t,     V = R + (S - R) t,     M = U + (V - U) t   (the new point)
       first half:  Q / M, U / M                      (each coordinate divided by M's)
       second half: (V - M) / (1 - M), (S - M) / (1 - M)

All eight splits match this to 1e-7, the precision of the stored values [als 12.4.6], and each half
plays as the unsplit segment did (0.03 dB rms or better). The halves are no longer mirrored, so a
split leaves Live's family. The point goes where it was placed, on the grid or not (beats
18.0226 and 30.8846).

## Dragging a curve

Dragging a segment with Alt (Option on macOS) held reshapes its curve. Two sets of hand drags,
each starting from known curves in four copies dragged by different amounts: curve-drag (56
drags of 14 shapes: Live's family, both extremes, edges, S curves, uneven and split halves) and
curve-drag-lopsided (48 of 12: lopsided S curves and curves whose control points cross the
diagonal; the fourth copy dragged twice). The rule below reproduces every one of the 104 saved
curves to 1e-4 [als 12.4.6].

**Each control point has a path:** a straight line from the corner (0, 1) to a point (p, p) on
the diagonal, then a straight line on to the corner (1, 0). The first leg is above the diagonal
(the value moves early), the second below it (the value moves late), and (p, p) is where that
control point lies on a straight line. The point's place on its path is F: 0 at (0, 1), 1 at
(p, p), 2 at (1, 0), evenly along each leg. From a control point (x, y):

| Where | p | F |
|---|---|---|
| above the diagonal (y > x) | x / (x + 1 - y) | x / p |
| below the diagonal (y < x) | y / (y + 1 - x) | 1 + (x - p) / (1 - p) |
| on the diagonal | x | 1 |
| top edge, left edge | 1, 0 | x, 1 - y |
| bottom edge, right edge | 0, 1 | 1 + x, 2 - y |

A drag changes F and **never changes p**. Live's family is the two paths with p = 1/4 and 3/4,
both points at the same F. A control point on an edge has p = 0 or 1, so its path is two edges
of the box: it slides along the edge, turns at the curve's own end, (0, 0) or (1, 1), and stops at
the other two corners.

**Where a drag starts.** A straight segment, a curve whose two points both lie on the diagonal
(it plays straight; seen with both at (0.5, 0.5)) and one whose two points are both in the
corners (0, 1) or (1, 0) have no p of their own: the drag starts on Live's family, p = 1/4 and
3/4. A single point on the diagonal keeps its own place as p (seen at (0.3, 0.3)). A single point
in a corner, with the other elsewhere, is not seen [measure].

**Steps.** Every drag moved F by a whole number of steps of exactly 1/64 (up to 91 in one drag;
in Live's family that is 1/256 of x1). How far the mouse moves per step is not measured.

**Two modes, chosen when the drag starts:**

- **Together:** both points on the same side of the diagonal, or both on it. Each step adds the
  same 1/64 to both F: the whole curve moves earlier or later.
- **Apart:** the points on opposite sides of the diagonal (an S or a reverse S, lopsided or not),
  or one exactly on it. Each step adds 1/64 to the F of the point with the larger F (the one
  below the diagonal) and takes 1/64 from the other's. Point symmetry plays no part: lopsided S
  curves (curve-drag-lopsided bars 1, 2, 3, 5, 6) and one with the points equally far from the
  diagonal but on unrelated paths (bar 4) all move apart.

The mode **holds for the whole drag**, even when the points pass each other's side: together,
one point crosses the diagonal first and the curve turns into a lopsided S on the way (bars 8, 9
and 10, copies 1 to 3); apart, an S passes through a straight line into the reverse S (curve-drag
bar 7, copy 4). **The next drag chooses again** from where the points are then. In the fourth
copy each of these two-drag results has one solution in whole steps:

| Bar | First drag | Then | Second drag |
|---|---|---|---|
| 1 | 30 steps apart | both points above the diagonal | 24 steps together |
| 3 | 44 steps apart | both above | 20 steps together |
| 8 | 22 steps together | on opposite sides | 46 steps apart |
| 9 | 28 steps together | on opposite sides | 52 steps apart |

**Direction.** The mouse direction that moves a curve later, together, is the one that, apart,
moves the point below the diagonal later and the other earlier: the S bends further. The other
direction flattens an S through a straight line into the reverse S. In curve-drag-lopsided each
bar's copies were dragged one way (copies 1, 2 and 4) or the other (copy 3), and the fitted steps
keep that sign through every change of mode. Which way on the screen moves a curve later, and whether it flips
between rising and falling segments, is not measured [measure].

**Ends.** A control point that would pass the end of its path (F below 0 or above 2) stops there
while the other goes on, changing the shape (curve-drag bar 6 copies 2 and 4, bar 8 copy 3, bar 9
copy 3). A step that would take every point still moving past its end is not taken, so a drag
can stop one step short of a corner: the symmetric S curves stopped at F = 1.990625 and 0.009375
(curve-drag bars 7 and 14 copy 3, bar 11 copy 4), and the lopsided set reached the corners
exactly where its steps landed on them (curve-drag-lopsided bars 3, 4, 7 copy 3).

A point that ends in a corner has lost its p (it is on every path). What the next drag does with
it is not seen [measure]; curve_drag.py assumes Live's family.

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

**Fast curves.** A curve steep enough to change faster than the ramp is smoothed as well.
utility-gain-splits beats 34 to 34.125 is a 62 ms segment, shaped by hand, whose control points
(0.648, 0.117) and (0, 0.596) make it fall about 4 dB in 8 ms. It plays 0.64 dB
rms off its Bezier, but 0.11 dB rms off the Bezier averaged over 4 to 6 ms and 1.75 ms late (a
box average and a smootherstep ramp fit alike). The jumps' ramps above are centred, not late; the
delay is from this one segment [measure].

## Open

- Which way on the screen a curve drag moves a curve later, and how far the mouse moves per step
  (Dragging a curve) [measure].
- Where a drag takes a control point that starts in the corner (0, 1) or (1, 0) while the other
  point is elsewhere [measure].
- The smoothing of a mute, and of a gain parameter's continuous motion faster than its ramp time
  [measure].
- Other parameter kinds: a frequency knob (logarithmic), a choice, a toggle [measure].
- Whether a lane interpolates in position for every device, plug-ins included [measure].
