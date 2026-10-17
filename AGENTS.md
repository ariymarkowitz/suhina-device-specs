# Notes for agents working in this repository

Read `README.md` first (clean-room rules, confidence tags) and `tools/README.md` before measuring.

## Talking to Live: use the Remote Script, not the window

Live 12 is driven through the **AbletonMCP Remote Script**, which runs inside Live and answers
JSON commands on `127.0.0.1:9877`. Use it through `tools/harness/live_check.py` (`PY` is
`tools/.venv/bin/python`):

| Task | Command |
|---|---|
| Is Live listening? | `nc -z 127.0.0.1 9877` |
| Open a set and wait until it is loaded | `$PY tools/harness/live_check.py open <set>.als` |
| Read every track's devices and parameter values | `$PY tools/harness/live_check.py read -o <file>.read.json` |
| Check a generated set against what it should hold | `$PY tools/harness/live_check.py verify <set>.cases.json -o <set>.verified.json` |
| Anything else the script offers | `live_check.Live().call("<command>", **params)` in Python |

The script's other commands include `get_session_info`, `get_track_info`, `get_device_parameters`,
`set_device_parameter`, `set_tempo`, `start_playback`/`stop_playback`, `get_arrangement_clips`
and browser access (`grep command_type` in
`~/Music/Ableton/User Library/Remote Scripts/AbletonMCP/__init__.py` lists them all).

- **Do not install or start the `ableton-mcp` project's MCP server.** Only its Remote Script is
  installed: the server can record sessions to a remote dataset. Talk to the socket directly, as
  `live_check.py` does.
- **Make sets as files, not by hand.** `make_als.py build` (one or a few runs) and `batch.py build`
  (many devices' runs in one set) write the measurement set; `live_check.py open` loads it and
  `verify` checks it. Do not use the Suhina Probe's Build cases button, drag files in, or change a
  measurement set through `set_device_parameter`: a set has to be reproducible from its cases files.
- If port 9877 is not listening, ask the user to start Live with AbletonMCP chosen as a Control
  Surface (`tools/README.md` › 2b). Do not fall back to clicking through Live instead.

## What still needs Live's window

Live's API has no audio export, and the Remote Script cannot arm, route or record tracks. So
**File › Export Audio/Video** is the one step that needs the UI. Settings are in
`tools/README.md` › 2, step 5: All Individual Tracks (or Selected Tracks Only), the probe's
length in bars, WAV, 32-bit, Normalize off, into the batch's `export/` folder, under the export
name the batch expects. Before taking control of Live's window, ask the user. They may prefer to
click the export themselves from the exact settings you give them. Settings dialogs, installing
the Suhina Probe and Max editing are also UI-only and the user's to do.

## Measuring and tests

- New behaviour runs go in a device folder's `runs.py` and through `tools/harness/batch.py`
  (check, build, analyse, summary); see its docstring.
- Run the tests with their output in a log file and read failures from it:
  `$PY -m unittest discover -s tools/harness/tests > <scratch>/tests.log 2>&1`.
- Renders (`export/`) and probe WAVs are not in the repository. Point every track's clip at the
  one shared probe file (the builders do), and do not copy probes into Live projects.
