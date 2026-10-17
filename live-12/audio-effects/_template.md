# <Device name> (manual 29.NN)

**Family:** <dynamics | EQ and filter | delay and looping | reverb and resonance | distortion | modulation and pitch | analysis and utility>
**Note status:** <draft | checked against Live | spec written>

## Summary

Two to four sentences in our own words: what the device does to the sound and what it is
typically used for.

## Signal flow

The order of the processing stages from input to output, as a list or an ASCII diagram, with
where the side-chain, feedback paths and dry/wet mix sit. Mark each stage with its tag.

## Controls

One table per section of the device's panel, in the order they appear on screen (left to right,
top to bottom). Use the exact control name as shown on the device.

| Control | Type | Range | Default | Unit / display | Taper | Notes | Tag |
|---|---|---|---|---|---|---|---|
| Frequency | knob | 20 Hz – 20 kHz | 1 kHz | Hz, kHz | logarithmic | ... | [manual] |

- **Type:** knob, slider, toggle, button, menu (list the options), number box, XY pad, display (editable or read-only), meter.
- **Range / Default:** as precise as known; `[measure]` when not known.
- **Taper:** linear, logarithmic, exponential, stepped (list the steps), or `[measure]`.
- Note in **Notes** what the control changes, when it is hidden or disabled (and by which other control),
  whether it is only in the expanded view, and modes in which it means something else.

### Context menu and hidden options

Options available only from the right-click menu, the title bar or a hidden view.

## Behaviour

What each control does to the signal, in enough detail to implement it: the curves, formulas,
filter types and slopes, envelope behaviour (attack/release shape, hold, lookahead), what
happens at range extremes, how the device behaves when modes switch while playing, latency it
reports, oversampling, stereo handling (linked, mid/side, independent), and what the
displays and meters show. Tag every claim.

## Edge cases

Behaviour at extremes and transitions: zero or infinite settings, feedback above 100 %,
tempo changes, transport start/stop, very low and very high sample rates, mono input, silence,
denormals, parameter jumps.

## Measurement plan

For every `[measure]` above: the test signal (sine sweep, impulse, noise, tone bursts at known
levels, a click track), the settings to try, what to read from the render (frequency response,
gain curve, envelope timing, delay times), and how to read parameter ranges and defaults (the
control's own display, a saved `.als`, the Live API's min and max of the parameter).

## Implementation notes

What a from-scratch implementation needs: the DSP building blocks (filters, delay lines,
envelope followers, oversampling) and published designs or open-source code that fit, with
their licences; the parts that are hard to match; and what the `.als` import has to map (the
device's XML element, each parameter element, its stored unit and the conversion), marked as
unverified until read from a saved set.

## Sources

1. Ableton Live 12 Reference Manual, 29.NN <Device>, https://www.ableton.com/en/live-manual/12/live-audio-effect-reference/#<anchor>
2. ...
