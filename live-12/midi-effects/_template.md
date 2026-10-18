# <Device name> (manual 30.N)

**Family:** <note generation | note transformation | control>
**Note status:** <draft | checked against Live | spec written>

## Summary

Two to four sentences in our own words: what the device does to the MIDI passing through it
and what it is typically used for.

## MIDI flow

The order of the processing stages from MIDI input to output, as a list or an ASCII diagram:
which messages each stage acts on (note-on, note-off, velocity, release velocity, pitch bend,
aftertouch, CCs, MPE per-note expression), which it passes through unchanged and which it drops,
and where the device's own clock or random generator enters. Mark each stage with its tag.

## Controls

One table per section of the device's panel, in the order they appear on screen (left to right,
top to bottom). Use the exact control name as shown on the device.

| Control | Type | Range | Default | Unit / display | Taper | Notes | Tag |
|---|---|---|---|---|---|---|---|
| Rate | chooser | 1/128 – 8 bars | 1/16 | note value | stepped (list) | ... | [manual] |

- **Type:** knob, slider, toggle, button, menu (list the options), number box, editable display, meter.
- **Range / Default:** as precise as known; `[measure]` when not known.
- **Taper:** linear, logarithmic, exponential, stepped (list the steps), or `[measure]`.
- Note in **Notes** what the control changes, when it is hidden or disabled (and by which other control),
  whether it is only in the expanded view, and modes in which it means something else.

### Context menu and hidden options

Options available only from the right-click menu, the title bar or a hidden view.

## Behaviour

What each control does to the MIDI, in enough detail to implement it: the formulas and curves
(velocity curves, pitch mappings), timing (how the device's clock follows the song tempo and
transport, when a pattern restarts, how rates are rounded to the beat, swing and groove), how
held notes, overlapping notes and chords are handled, what happens to the note-off of a note
whose pitch or timing was changed, the probability distributions behind random choices, latency
it reports, what Scale Awareness does, MPE pass-through, and what the displays show. Write times
in seconds, beats or bars, never in ticks or samples. Tag every claim.

## Edge cases

Transport start and stop, tempo changes, loop jumps, notes held across the loop end, the same
pitch played twice, pitches pushed past 0 or 127, velocities at 1 and 127, zero-length and very
long notes, sustain pedal, all-notes-off and panic, the device switched off while notes are held,
parameter changes while notes are held.

## Measurement plan

For every `[measure]` above: the input (a MIDI clip of known notes written with the AbletonMCP
Remote Script, AGENTS.md), the settings to try, and what to read from the output. Two ways to
observe the output: route the device's track into a second MIDI track and record it (recording
needs Live's window), or play an instrument with a known response after the device and analyse
the rendered audio (the existing harness). Say which fits. Ranges, defaults, steps and display
text come from the Live API (the Suhina Probe's dump or the Remote Script's
`get_device_parameters`) and stored values from a saved `.als`.

## Implementation notes

What a from-scratch implementation needs: the event-processing structure (a per-block MIDI
event list, a scheduler for delayed or generated notes, a held-note table for matching
note-offs), a seeded random generator where the device is random, published designs or
open-source code that fit with their licences, the parts that are hard to match, and what the
`.als` import has to map (the device's XML element, each parameter element, its stored unit and
the conversion), marked as unverified until read from a saved set.

## Sources

1. Ableton Live 12 Reference Manual, 30.N <Device>, https://www.ableton.com/en/live-manual/12/live-midi-effect-reference/#<anchor>
2. ...
