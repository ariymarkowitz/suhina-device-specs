# Brief: put the Live 12.4.6 parameter dump into the device notes

Work only in `/Users/ari/Documents/code/suhina-resources`. Edit only the notes you are given
(`live-12/audio-effects/29.NN-*.md`). Do **not** edit `INDEX.md`, `common.md`, `_template.md` or
anything under `tools/` or `measurements/`. Do not read `measurements/dump-12.4.6.json` (2.5 MB):
everything you need is in `measurements/dump-12.4.6-summary/<Element>.txt`, one per device.
Read `README.md` (clean-room rules and tags) once before starting.

## What the summaries are

Each summary was produced by the Suhina Probe in Live 12.4.6 from a device freshly loaded from
the browser (so Live's factory default preset). Per parameter: the Live API name (and
`original_name` if different), the internal min..max, the **loaded value** and its display text,
the **reset value** (`default_value`, what double-click/Delete restores) and its display, the step
list (stepped controls) or a rough taper, and the display text at 9 evenly spaced internal values.
At the end: the parameter elements of that device in a saved set, with stored values. Those are
in the `.als`'s own units (often physical: Hz, ms, linear gain where 1 = 0 dB), not the API's
internal range.

## What to do in each note

1. **Controls tables.** For each control that the dump covers, replace `[measure]` (and
   "believed …" guesses) with the dump's fact, tagged `[dump 12.4.6]`:
   - **Range**: the first and last display texts (e.g. `−inf dB to 6.00 dB`). Keep a different
     range from a `[source: N]` (often a Max wrapper's DSP-level bounds) and say which is the
     panel's: "panel −inf to 6 dB [dump 12.4.6]; the DSP object accepts −70.6 to +6 dB [source: 8]".
   - **Default**: the loaded value's display (what a user gets from the browser). When the reset
     value differs (e.g. loads as Log, resets to Lin), say both: "Log (loaded preset); resets to
     Lin [dump 12.4.6]". Ignore the reset value of `Device On`, which is a Live API quirk.
   - **Steps**: the full list for stepped controls.
   - **Taper**: from the samples, in words: "logarithmic (0.01 ms at 0, 3.16 ms at mid, 1 s at
     top)", "linear in dB", "non-linear, finer near 1 (2:1 at mid, 4:1 at 0.75)". The `taper:`
     word in the summary is a rough fit; trust the samples. Give two or three anchor points when
     the taper is unusual; that is what an implementer needs.
   - **Unit / display**: the display format (decimals, unit switch such as ms → s at 1 s,
     `inf : 1` at the top).
   - Controls the dump lists that the note lacks: add a row (tag `[dump 12.4.6]`). Controls the
     note has that the dump lacks (view switches, meters, choosers that are not parameters): leave
     them as they are.
   - Where the dump contradicts a `[manual]` or `[source: N]` value, keep both and say which is
     the panel's.
2. **Implementation notes › `.als` import.** State the element name as fact (from the summary
   header) and drop "(unverified)". Replace guessed parameter element names with the real list
   from the summary's last section, tagged `[als 12.4.6]`, noting the stored units where they
   differ from the display (e.g. "Threshold stored as linear gain, 1 = 0 dB").
3. **Sources.** Add, as the next number in that note's list:
   `Parameter dump of Live 12.4.6 by the Suhina Probe (measurements/dump-12.4.6.json, 2026-10-18) and the set saved from it (measurements/populate-12.4.6.als); tags [dump 12.4.6] and [als 12.4.6]`.
   Do not edit the README's tag list; the coordinator adds the two tags there.
4. **Measurement plan.** Strike or shorten items the dump has answered (ranges, defaults, steps,
   tapers, units). Leave behaviour items (curves, times, filter shapes) as they are.
5. **Status line** at the top: change `**Note status:** draft` to `**Note status:** dump checked`.
6. Leave every behaviour `[measure]` (curves, times, sounds) alone.

## Style and rules

- Facts in your own words. Control names, ranges, units, defaults and step names are facts and
  can be written as they are; never copy sentences from anywhere.
- Keep each note's existing structure, table columns and voice. Change only what the dump settles.
- Use the Unicode minus (−) in prose and tables if the note already does; keep the display text
  as Live shows it otherwise.
- Don't invent: if the summary is ambiguous for a control (for example two controls share a name
  and you cannot tell which is which), say so in the row rather than guessing.

## Report back (short)

Per note: number of `[measure]` items replaced, any dump/source contradictions you recorded, any
parameter you could not match to a control, and anything odd in the dump (e.g. a display that is
not monotonic, a range that looks wrong).
