# Reference data from Live 12.4.6

Read from Live itself through its public interfaces (`tools/README.md` › 1 and 2b), once per Live
version. Measurement runs and the notes' `[dump 12.4.6]` and `[als 12.4.6]` facts depend on them.

| File | What |
|---|---|
| `dump-12.4.6.json` | every audio effect's parameters: range, default, step list, display text at 65 values across the range (so taper and unit). Made by the Suhina Probe's Dump (`tools/probe-device/`) |
| `dump-12.4.6-summary/` | the same, one readable text file per device, with the stored values from the saved set beside the API's |
| `populate-12.4.6.als` | a set saved by Live holding a fresh copy of every audio effect: the `.als` element names and stored values; also the source `make_als.py` copies devices from |
| `als-map-12.4.6.json` | for each device, how each API parameter becomes a stored element and value (`make_als.py map`; `tools/README.md` › 2b). Needed to build any measurement set |
| `dump-midi-12.4.6.json`, `populate-midi-12.4.6.als`, `populate-midi-12.4.6.read.json` | the same for the MIDI effects (`tools/harness/populate_midi.py`) |
| `midi-effects.recorded.json` | the recording of every MIDI effect's output the MIDI notes were read from (`midi_set.py read`) |

Do not overwrite these with another Live version's: add files for that version beside them.
