# Controls and behaviour many MIDI effects share

Device notes link here instead of repeating these parts. Where a device departs from what is
written here, its own note says so. The eight devices of manual chapter 30 are Arpeggiator,
CC Control, Chord, Note Length, Pitch, Random, Scale and Velocity ([INDEX.md](INDEX.md)). Their
Live 12.4.6 parameter dump (`measurements/dump-midi-12.4.6.json`, summaries in
`measurements/dump-12.4.6-summary/Midi*.txt`) is in each device note's Controls; this file has
not been revised against it, so everything below is `[manual]`, `[source: N]`, `[inferred]` or
`[measure]`. Sources are listed at the bottom.

The manual says very little about how these devices treat note-offs, non-note messages and MPE;
most of that is therefore `[inferred]` or `[measure]` here, with the release-note fixes as the
only hard evidence of intent. The Measurement plan at the end of this file is the shared way to
observe a MIDI effect's output; the device notes refer to it.

## Which device has what

| Device | Family | Use Current Scale (title bar) | Own Root / Scale choosers | Tempo sync | Groove | Notes |
|---|---|---|---|---|---|---|
| Arpeggiator | note generation | yes, since 12.0 [source: 2] | yes (disabled while Use Current Scale is on) [manual] | Rate Sync / Free, Retrigger Interval, Velocity Decay [manual] | own Groove chooser [manual] | collapse/expand toggle in the title bar since 12.0 [source: 2] |
| CC Control | control | no [manual] | no | none | none | 16 controls in two pages of 8; new in 12.0 [source: 2] |
| Chord | note generation | yes, since 12.0 [source: 2] | [measure] | Strum timing, whether synced is [measure] | none [measure] | |
| Note Length | note transformation | no [manual; source: 1] | no | Time mode, Sync [measure] | none [measure] | |
| Pitch | note transformation | yes, since 12.0 [source: 2] | [measure] | none | none | |
| Random | note transformation | yes, since 12.0 [source: 2] | [measure] | none | none | |
| Scale | note transformation | its parameters follow the clip's scale since 12.0 [source: 2] | Base and Scale Name choosers | none | none | |
| Velocity | note transformation | no [manual; source: 1] | no | none | none | |

The manual's own list of scale-aware MIDI effects is Arpeggiator, Chord, Pitch, Random and Scale
[manual; source: 7]. Chapter 30's introduction says the pitch controls of these effects work in
scale degrees when Use Current Scale is on [manual; source: 1].

## The title bar

- **Device on/off** (the activator at the left of the title bar): the device is bypassed as if it
  were not in the chain: the signal passes through unprocessed and the device uses no CPU
  [manual; source: 6]. The manual does not say what happens to notes the device is holding or
  has generated when it is switched off while notes sound. See [Switching a device off while
  notes sound](#switching-a-device-off-while-notes-sound).
- **Use Current Scale** toggle (Arpeggiator, Chord, Pitch, Random, Scale; see [Scale Awareness](#scale-awareness)).
  It sits in the title bar, not on the panel [manual; source: 1].
- **Collapse/expand toggle** in the title bar: Arpeggiator got one in 12.0 [source: 2]; whether
  the other MIDI effects have one is [measure] (a view feature; not part of the audio path).
- **CC Control** has two toggles in its title bar that choose controls 1 to 8 or 9 to 16, a Send
  button and a Learn toggle [manual]; see [30.02-cc-control.md](30.02-cc-control.md).
- The context menu, hot-swap, preset saving and the Rack macro mapping are host features, not
  part of the device. Parameters of any of these devices can be mapped to Rack macros; for
  Arpeggiator's and Scale's Root and Scale choosers this works since 12.1.5 [source: 2].
- Every MIDI effect lives left of the instrument on a MIDI track, or in a MIDI Effect Rack, or
  left of the instrument in an Instrument Rack or a Drum Rack chain; audio effects cannot be
  placed there and MIDI effects cannot be placed after an instrument [manual; source: 5, 6].

### Switching a device off while notes sound

The manual does not describe it [source: 6]. The behaviour matters because a bypassed
generator (Arpeggiator, Chord with Strum) may hold notes the next device never sees ended.

- Expected [inferred]: the notes that the device has output and not yet ended are ended (a
  note-off is sent) at the moment of bypass, the incoming notes that are still held go through
  unchanged, and notes that were held at the input before the switch-off are not started
  retroactively (no note-on arrives for them).
- The cases that could leave a stuck note: a note started while the device was active and ended
  while it is inactive; the reverse; a transposing device (Pitch, Scale, Chord) that changed the
  pitch of the note-on, so that a plain pass-through of the real note-off no longer matches.
  Each is a row in the shared Measurement plan (case C1).
- 12.1 fixed a deactivated Chord device that still altered per-note pitch bend while following a
  scale [source: 2]: so a bypassed device must not alter anything, MPE data included.

## Scale Awareness

What the manual says:

- A clip has a **Scale Mode** toggle (Clip View or the Control Bar) and a **Root Note** and a
  **Scale Name** chooser next to it. The settings apply to the selected clip, or to clips created
  afterwards when none is selected; with several clips selected the Control Bar sets them all
  [manual; source: 7].
- A scale-aware MIDI effect has **Use Current Scale** in its title bar. When it is on, the
  clip's current scale is applied and pitch parameters are set in scale degrees instead of
  semitones [manual; source: 1, 7]. In the Arpeggiator the Root and Scale choosers are disabled
  while it is on [manual].
- Auto Shift's Quantizer and Meld's oscillators and filters are also scale aware; the audio
  effects Auto Pitch (12.1), Resonators and Spectral Resonator (12.2) follow [manual; source: 2];
  see the audio-effects [common.md](../audio-effects/common.md).

What the release notes add:

| Version | Change |
|---|---|
| 12.0 | Arpeggiator, Chord, Pitch, Random and Scale got a Use Current Scale toggle. With an active clip scale the Scale device's parameters follow the clip's Root Note and Scale Name, and the effective root and scale are shown in the Base and Scale choosers. Per-note pitch bend of incoming MPE notes is transformed so that bent notes stay in the scale (Arpeggiator, Chord, Pitch, Random) [source: 2] |
| 12.1 | Audio clips can have a scale (passed to scale-aware devices, playback unchanged). Tracks with a Drum Rack can have a scale, used by the devices that have Use Current Scale on. Fixed devices not starting with the right scale when no clip was playing on the track [source: 2] |
| 12.1.5 | Scale and Root can be mapped to Rack macros in Arpeggiator and Scale [source: 2] |
| 12.1.10 | Fixed wrong per-note pitch bend handling in Pitch, Random and Arpeggiator with scale awareness on when the incoming note was not in the scale [source: 2] |
| 12.2 | Sets with an unknown scale name load; the unknown scale is replaced by the default major scale [source: 2] |
| 11.1 | (Scale device) no longer cuts off played notes when the scale is a single note [source: 3] |

Deductions and gaps:

- The scale a device sees is a property of the **track**, set by the clip that is playing on it
  [inferred from 12.1: Drum Rack tracks "can have a scale", devices initialise with the right
  scale "when no clip was playing"]. What scale applies while no clip plays (a live-played
  track, the last clip played, the selected clip), and when a change of clip changes it
  (launch, or the clip's own start) are [measure].
- **No scale** (Scale Mode off in the clip) with Use Current Scale on: the manual does not
  say. The sibling device Meld uses a major scale built on the incoming note in that case
  [source: 2, 12.2]; the MIDI effects may use the 12-tone chromatic scale (scale degrees equal
  semitones) or the device's own Root and Scale [measure].
- **Tuning systems.** When a tuning system is loaded the Scale Mode choosers in Clip View and
  the Control Bar are hidden and the Use Current Scale toggle on devices is disabled
  [manual; source: 8]. Drum Racks bypass tuning [manual; source: 8].
- **Scale degrees.** With Use Current Scale on, an offset of +n degrees means n steps up the
  scale from the note, counting from the note's own position when the note is in the scale
  (for a pentatonic scale an octave is 5 degrees, not 12) [inferred]. What a note outside the
  scale does first (snapped down or up, or counted from the nearest degree), and how a
  degree offset wraps at the octave, are [measure]; each device note has its own cases.
- **Root / Scale choosers' lists.** The names are the clip's Scale Name list (Major, Minor,
  the modes, pentatonics, and so on); the list is shared with the clip's chooser [inferred].
  The exact list belongs to the scale-aware audio effects too and is [measure] once, in
  [30.07-scale.md](30.07-scale.md).
- The chooser's **Root note** and scale name are saved with the device (and the clip stores its
  own); an `.als` import has to take both [inferred; measure].

## Sync to the song tempo and transport

Only the Arpeggiator (Rate, Retrigger Interval, Velocity Decay) and probably Note Length
(Time mode) and Chord (Strum) have time controls [manual; measure].

- **Sync / Free.** A Sync toggle chooses between rates in note values of the song tempo and
  rates in milliseconds [manual]. In Sync mode the rate follows tempo changes [manual].
- **Note values.** The lists differ per device and are not printed in the manual. They are
  fractions of a **whole note (4 beats)**: 1/16 is a sixteenth, 1/16 of 4 beats = 0.25 beats.
  Whether triplets (1/16T style) and dotted values appear in each list, and how they are
  named, is [measure]. A forum report says that the Arpeggiator's rate 24 gives a triplet feel
  and 32 gives thirty-second notes [source: 9], so the list is written as denominators of a
  whole note (1/24 is a sixteenth triplet).
- **How a device's clock restarts.** The manual for Retrigger says "Beat" retriggering is
  aligned to the song position, in notes or bars [manual; source: 14]: the position in the
  song, not the time since a key was pressed, decides when the next step falls. So a synced
  rate is a **grid locked to the song's beat time**, not a timer started by the first note
  [inferred]. 12.4 added: in Synced mode, a first note arriving within 5 ms after a grid
  division starts the sequence immediately, otherwise it waits for the next division
  [source: 2]; this reads as a grace period for a note played slightly late.
- **Transport stopped.** A device's tempo grid keeps running when Live's transport is stopped,
  so a played arpeggio still follows the tempo [inferred from ordinary use; measure]. Where the
  grid is after the transport starts or stops (restarts at bar 1, or continues from the song
  position) and what happens at a jump of the song position, a locator or a loop end
  are [measure]. 12.2 fixed an Arpeggiator whose notes skipped or repeated when the
  arrangement timeline looped [source: 2].
- **Tempo changes** (automation or a tap tempo) change the interval of the next step at once;
  a step that is already scheduled is not moved [inferred; measure].
- **External sync, Link.** Live's time base follows MIDI clock, Link or the Tempo Follower as the
  song tempo [manual; source: 12]; nothing special is said for MIDI effects.
- **Never in samples.** A step lands on a sample-accurate time in the track's buffer, but a
  Suhina device is specified in beats and seconds (AGENTS.md).

### Groove

- The Arpeggiator has its own **Groove** chooser; it behaves like a clip's groove: swing and
  timing are taken from a groove file chosen in the chooser, and the **Global Groove Amount**
  (Groove Pool, Control Bar) sets the strength [manual; source: 1, 14].
- A groove has Base, Quantize, Timing, Random and Velocity (−100 to +100 %) values, and the
  Global Amount scales Timing, Random and Velocity, goes up to 130 % and applies 100 % as
  stored [manual; source: 9]. Which of these the Arpeggiator uses (timing, velocity, or both)
  is [measure].
- 12.2 fixed a groove not being applied when the Arpeggiator's Gate was between 75 % and
  100 % [source: 2]; so the groove acts on the **start time** of each step and Gate is
  measured from the shifted start [inferred].
- The other MIDI effects have no groove chooser. Whether a clip's own groove applies to the
  notes before the effects (it does for MIDI clips: Live moves the notes before they reach the
  device chain) [inferred; measure].

## Note-offs, held notes and other messages

The manual never states these rules. The parts below mix what the release notes show with the
usual structure of a MIDI processor.

- **Note-on / note-off pairing.** Every device that changes a note's pitch, time or channel
  must keep a table of the notes it sounded so that the matching note-off ends the same
  output note, even if the parameter changed in between [inferred]. How each device pairs
  (by the input note, per input channel) is in its own note. Open for all: a parameter
  changed while a note is held (is the note-off pitch the old or the new one) and the same
  pitch started twice (overlapping) [measure].
- **Pitches pushed past 0 or 127** (Pitch, Chord, Random, Scale, the Arpeggiator's
  transposition): dropped, clamped or folded back into range is not documented for any device
  [measure]; Pitch's Mode (Block, Fold, Limit) is the only control that addresses a range, and it
  is the user's chosen window, not the MIDI limits. Each device note has a case at the extremes.
- **Randomness** (Arpeggiator's Random styles, Chord's Chance, Random): no device has a seed
  control, and whether the generator restarts at transport start (the same result each play) or
  runs on (a new result each play) is [measure]. Play the same clip twice from the start and
  compare.
- **Velocity 0 note-on** is a note-off, as is usual in MIDI [inferred]; the devices and the
  clip engine see notes as note-on/note-off pairs anyway.
- **Release velocity.** Note Length has a release-velocity control (Rel Vel); MPE-aware Max
  for Live effects pass the note-off velocity (11.3.10, MPE Control) [source: 2, 3]. Whether the
  built-in effects pass the release velocity of the incoming note unchanged is [measure].
- **Non-note messages** (CC, pitch bend, channel pressure, polyphonic aftertouch, program
  change): the manual does not list any of the eight devices as filtering them, so they are
  passed through in time [inferred]. Rack chain selection filters only notes by default; the
  Chain Select ruler's "Chain Selector Filters MIDI Ctrl" option filters all MIDI events
  [manual; source: 5]. Nothing is said about key/velocity zones and CCs.
- **MPE.** Live 11 added MPE support "to all built-in MIDI effects" so per-note expression
  passes through them [source: 3]. Known details:
  - Per-note pitch bend, Slide (CC 74) and Pressure ride on a note; an effect that moves a note
    to another time or pitch should move the expression with it [inferred].
  - The Arpeggiator can modulate the **root notes** of an arpeggio with MPE; the notes that the
    device generates itself by transposing (Distance/Steps) do not get MPE modulation
    [source: 3, Live 11.0].
  - Chord (12.0) sends per-note MPE data to the notes it generates; with scale awareness on, bent
    chords stay in the scale [source: 2].
  - 12.1: fixed MPE not being sent correctly when the Arpeggiator or Note Length sits inside or
    after a MIDI Effect Rack, and the two devices stopped sending superfluous MPE events
    [source: 2].
  - 12.1: per-note expression did not reach instruments that apply MPE relatively when
    Chord's Strum was nonzero; fixed [source: 2].
  - 11.0.10: MPE data through MIDI Effect Racks crashed Live; fixed [source: 3].
  - Live's default MPE pitch-bend range assumed by the effects (48 semitones for tuning
    system compatibility is mentioned for instruments [source: 8]) and the channel the
    output notes use are [measure].
- **Channels.** A MIDI track normally carries channel 1 to 16 as set by the track's input;
  an MPE input locks the routing to All Channels [manual; source: 10]. Output channel of a
  generated note is the input note's channel unless the note says otherwise [inferred;
  measure].
- **Hold and sustain pedal.** The Arpeggiator's Hold is its own; CC 64 at the input is a
  plain CC (passes through) [inferred]. Whether a sustained (pedal) note counts as held for
  the Arpeggiator is [measure].
- **All notes off / panic.** Stopping the transport sends note-offs for notes that clips are
  holding; an effect that has delayed or generated notes must end them at the same time
  [inferred; measure] (case C3).

## MIDI effects in racks and tracks

Only as far as it bears on a device's behaviour [source: 5]:

- A **MIDI Effect Rack** takes MIDI effects only and goes on MIDI tracks. Every chain receives
  the same incoming MIDI at the same time; the chains' outputs are **merged** and passed to the
  next device [manual]. So a note that two chains each transform comes out as two notes; two
  chains that output the same pitch at the same time (a doubled note) are two note-ons, and
  whether the receiving instrument sees one or two note-offs ends them correctly is
  [measure].
- Each chain has a **key zone, velocity zone and chain selector zone**; a note must pass all
  three to reach the chain's devices [manual]. Key and velocity fade ranges lower the velocity
  of notes entering the chain; so do chain selector fades [manual]. Zones filter on the note
  that arrives at the chain, **before** the chain's devices; a Pitch or Chord device in the
  chain does not change which chain the note went into [inferred].
- The chain select zones filter only notes by default; CCs pass unless the Chain Selector
  Filters MIDI Ctrl option is on [manual].
- In an **Instrument Rack** and a **Drum Rack chain**, the MIDI effects run before the
  instrument. A Drum Rack chain only receives its Receive note (or all notes when Receive is
  All Notes); the note arrives at the chain's MIDI effects with the pad's note, and a
  transposing effect is applied after the Receive note was matched [manual; inferred].
- **Chain Auto Select** (12.1: stored in Audio Effect, Instrument and MIDI Effect Rack presets
  [source: 2]) lights the chains that currently process signal; not an audio-path feature.
- **Selecting several chains** and editing a parameter changes it in all of them (12.0)
  [source: 2]; a UI feature.
- **Order.** Devices run left to right, so the order matters (Pitch before Scale gives a
  different result from Scale before Pitch) [manual; source: 6].
- **Routing another track.** A MIDI track that takes its input from another track receives the
  MIDI after the source track's MIDI effects and before the source instrument [manual;
  source: 11]. This is how the output of a MIDI effect is recorded (Measurement plan).

## Latency

- Live compensates for the delay of built-in devices and plug-ins automatically (Delay
  Compensation option) [manual; source: 6]. The page does not address MIDI-only devices.
- No source reports a plug-in-delay latency for any of the eight MIDI effects [measure]. They
  have no look-ahead that needs one, with a possible exception: a device that has to know a
  note's length before acting (Note Length in some modes, Velocity?) would have to delay it
  [measure]. An effect that quantises to a grid (Arpeggiator in Sync mode) delays the first
  note up to one step; that is musical timing, not reported latency [inferred].
- MIDI timing in Live is accurate to the audio buffer: notes carry timestamps within the
  buffer and the monitoring adds the buffer's delay [manual; source: 13]. A Suhina device
  keeps each event's sample offset within the block.
- To measure: put a MIDI clip with one note at a known position through the device with
  everything neutral; record the output (Measurement plan, case C2) and compare note-on times
  with the input's, once with the delay compensation option on and once off.

## Changes in Live 12 that touched several MIDI effects

Collected from the release notes [source: 2], newest first for each topic.

| Topic | Change |
|---|---|
| Scale awareness | 12.0 Use Current Scale in Arpeggiator, Chord, Pitch, Random, Scale; 12.1 audio and Drum Rack track scales; 12.1.5 Scale and Root can be mapped to Rack macros; 12.1.10 pitch-bend fix when out of scale; 12.2 unknown scale names |
| MPE | 12.0 Arpeggiator, Pitch, Random transform per-note pitch bend in scale; Chord sends per-note MPE; 12.1 MPE fixes in MIDI Effect Racks (Arpeggiator, Note Length); 12.1 Chord strum expression fix |
| MIDI Effect Racks | 12.0 several selected chains edit together; 12.1 Chain Auto Select saved in presets |
| New device | 12.0 CC Control; 12.1 its Learn mode; 12.3 an extra parameter bank for control surfaces |
| Arpeggiator | 12.0 redesign (Style, Hold, Offset, Groove, pattern display); 12.1.5 bipolar Distance; 12.2 groove and looping fixes; 12.4 5 ms synced grace period and Max for Live MIDI effect fix |
| Chord | 12.0 Strum, Strum Tension, Strum Crescendo, Velocity/Chance toggle, Learn, LEDs |
| Pitch | 12.0 Step Down/Up buttons, Step Width, Mode (Block, Fold, Limit) |
| Random | 12.0 Scale renamed Interval, Mode split into Random and Alt toggles |
| Note Length | 12.0 Latch mode, Gate and Length swapped, Time mode split into two buttons, "Release Vel." renamed Rel Vel, "Decay Time" renamed Decay |
| Scale | 12.0 parameters follow the clip's scale; info text |

(Details live in the device notes; the table is for orientation.)

## Measurement plan shared by the MIDI effects

Observing a MIDI effect means reading the MIDI that leaves it. Two ways [source: 11]:

1. **Record the output (preferred).** Track A holds the input clip (written with the Remote
   Script's `create_midi_track`, `create_clip`, `add_notes_to_clip`) and the device under test,
   followed by no instrument. Track B is a MIDI track whose input is Track A (tap after
   Track A's MIDI effects) and which is armed. Fire A's clip while B records a clip; the notes
   of B's clip are read back with the Remote Script's `get_clip_notes`. The routing, arming and
   recording are UI steps (the Remote Script cannot arm, route or record: AGENTS.md); ask the
   user first. One recording gives the note starts, lengths, pitches and velocities with
   Live's own quantisation of MIDI recording to be accounted for: record with the clip's
   start at a bar and read start times as fractions of beats; Live records at its sample
   timing, so a time resolution of a few ms is expected [measure]. `get_clip_notes` returns notes
   only: recorded CCs, pitch bend and per-note MPE envelopes (CC Control, case C5, C7) are read
   from the saved `.als` of the recording.
2. **Play an instrument with a known response** after the device and analyse the rendered audio
   through the harness (`tools/README.md` › 2). Fits timing and velocity checks; it cannot show
   note-offs of the generated notes unless the instrument's release is long and the note
   lengths are read from the amplitude envelope. A sine instrument with a short release is
   enough for pitch and onset checks.

Shared cases (the device notes name them):

- **C1. Switch-off with held notes.** Hold a chord for 8 beats; switch the device off at beat
  4 (automation of the device On, or `set_device_parameter` once; AGENTS.md forbids this for
  measurement sets, so write the automation in the clip's device envelope or use the
  Arrangement) and read whether a note-off for each sounding note arrives and when; then
  switch on at beat 6 with the chord still held.
- **C2. Latency.** One note at beat 1, device neutral; compare times with delay compensation on
  and off.
- **C3. Stop with generated notes sounding.** Stop the transport during a held arpeggio or a
  strummed chord; read the ends.
- **C4. Scale degrees.** A clip with scale C major and Use Current Scale on, notes C3 to
  C4 each in turn, each device's pitch control at +1, +2 and −1 degrees; then scale D Dorian
  and a pentatonic; then Scale Mode off; then a note outside the scale (C#3).
- **C5. MPE.** An MPE clip with per-note pitch bend, slide and pressure envelopes on a note;
  read the three expressions on the output notes (the note expression lanes of the recorded
  clip).
- **C6. Rack.** The device in two parallel chains of a MIDI Effect Rack, with the same and
  with different key zones; read doubled notes and their note-offs.
- **C7. Non-note messages.** CC 1, CC 64, pitch bend and channel pressure at the input of
  a clip (clip envelopes) around a note; whether they arrive and when.

## Sources

1. Ableton Live 12 Reference Manual, chapter 30 Live MIDI Effect Reference (introduction and
   30.1 – 30.8), https://www.ableton.com/en/live-manual/12/live-midi-effect-reference/ (the
   page text is read through a summarising fetcher; wording is ours).
2. Ableton, Live 12 release notes, https://www.ableton.com/en/release-notes/live-12/ (read at
   offsets 0, 100 000 and 200 000 of a page of about 304 000 characters; the entries here are
   from 12.0 to 12.4).
3. Ableton, Live 11 release notes, https://www.ableton.com/en/release-notes/live-11/ (11.0 to
   11.3.40; Arpeggiator's MPE root modulation, "MPE support in all built-in MIDI effects",
   11.0.10, 11.1, 11.3.10).
4. Ableton, Live 10 release notes, https://www.ableton.com/en/release-notes/live-10/ (10.0.6:
   Arpeggiator played at half rate when Gate was set to 100 by typing; read to 10.0.2 only).
5. Ableton Live 12 Reference Manual, Instrument, Drum and Effect Racks,
   https://www.ableton.com/en/live-manual/12/instrument-drum-and-effect-racks/
6. Ableton Live 12 Reference Manual, Working with Instruments and Effects (device chain,
   activator, delay compensation), https://www.ableton.com/en/live-manual/12/working-with-instruments-and-effects/
7. Ableton Live 12 Reference Manual, Live Concepts › Scale Awareness (3.13) and Editing MIDI,
   https://www.ableton.com/en/live-manual/12/live-concepts/ ,
   https://www.ableton.com/en/live-manual/12/editing-midi/
8. Ableton Live 12 Reference Manual, Using Tuning Systems,
   https://www.ableton.com/en/live-manual/12/using-tuning-systems/
9. Ableton Live 12 Reference Manual, Using Grooves, https://www.ableton.com/en/live-manual/12/using-grooves/ ;
   Ableton forum, "Ratchet sequencing with Live 9 Arpeggiator?", https://forum.ableton.com/viewtopic.php?p=1659513
   (rates 24 and 32, unverified user report)
10. Ableton Live 12 Reference Manual, Editing MPE, https://www.ableton.com/en/live-manual/12/editing-mpe/
11. Ableton Live 12 Reference Manual, Routing and I/O, https://www.ableton.com/en/live-manual/12/routing-and-i-o/
12. Ableton Live 12 Reference Manual, Synchronizing with Link, Tempo Follower, and MIDI,
    https://www.ableton.com/en/live-manual/12/synchronizing-with-link-tempo-follower-and-midi/
13. Ableton Live 12 Reference Manual, MIDI Fact Sheet (timestamps, latency and jitter),
    https://www.ableton.com/en/live-manual/12/midi-fact-sheet/
14. Ableton Live 11 Reference Manual, 25 Live MIDI Effect Reference (Arpeggiator, Chord, Pitch,
    Random, Scale, Velocity, Note Length), https://www.ableton.com/en/live-manual/11/live-midi-effect-reference/
