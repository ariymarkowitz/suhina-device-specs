# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Makes the set the MIDI effects' parameter dump is taken from: the Suhina Probe on an audio
track and one MIDI track per Live 12 MIDI effect, each holding a fresh copy of that device.

    python populate_midi.py write -o measurements/populate-midi-gen.als
    python live_check.py open measurements/populate-midi-gen.als
    python populate_midi.py load
    # in Live: Dump parameters on the probe, then save the set (the UI steps)

The 2026-10-18 run wrote the set, loaded the devices, dumped them to
`measurements/dump-midi-12.4.6.json` and saved the set; Live saved it into a Project folder,
and the copy beside the dump is `measurements/populate-midi-12.4.6.als`. Do not write over that
saved set: it is the record the `[als 12.4.6]` facts of the MIDI effect notes come from.

`write` takes the tracks from a set Live saved (`measurements/populate-12.4.6.als`): its audio
track with the probe, and its empty MIDI track, copied once per MIDI effect and named after it.
No device element of a MIDI effect is known before Live has saved one, so `load` puts the
devices in afterwards through the AbletonMCP Remote Script: each track gets the browser's item
of the same name from the MIDI Effects category, which loads the factory default preset, as
the probe's Populate does for the audio effects with `Track.insert_device`.
"""

import argparse
import os
import sys

import als
import live_check

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCE = os.path.join(ROOT, "measurements", "populate-12.4.6.als")
PROBE = os.path.join(ROOT, "tools", "probe-device", "Suhina Probe.amxd")
PROBE_TRACK = "3-Audio"
MIDI_TRACK = "1-MIDI"

# Live 12 MIDI effects (manual chapter 30), by the names the browser shows.
MIDI_EFFECTS = ["Arpeggiator", "CC Control", "Chord", "Note Length", "Pitch", "Random",
                "Scale", "Velocity"]


def point_probe(track, set_dir):
    """Points the probe device's file reference at this checkout's Suhina Probe.amxd."""
    for ref in track.iter("FileRef"):
        rel = ref.find("RelativePath")
        if rel is None or not rel.get("Value", "").endswith("Suhina Probe.amxd"):
            continue
        ref.find("Path").set("Value", PROBE)
        rel.set("Value", os.path.relpath(PROBE, set_dir))
        ref.find("OriginalFileSize").set("Value", str(os.path.getsize(PROBE)))


def cmd_write(a):
    root = als.read_set(a.source)
    probe = als.find_track(root, PROBE_TRACK)
    midi = als.find_track(root, MIDI_TRACK)
    als.remove_returns(root)
    als.clear_tracks(root)
    ids = als.Ids(root)
    t = als.add_track(root, probe, "Probe", list(als.devices_holder(probe)), ids)
    point_probe(t, os.path.dirname(os.path.abspath(a.output)))
    for name in MIDI_EFFECTS:
        als.add_track(root, midi, name, [], ids)
    ids.close()
    als.write_set(root, a.output)
    print(f"wrote {a.output}: Probe and {len(MIDI_EFFECTS)} MIDI tracks")


def cmd_load(a):
    live = live_check.Live(timeout=120.0)  # the first browser query after Live starts is slow
    items = live.call("get_browser_items_at_path", path="midi_effects").get("items", [])
    uris = {i["name"]: i["uri"] for i in items if i.get("uri")}
    info = live.call("get_session_info")
    failed = []
    for i in range(int(info["track_count"])):
        t = live.call("get_track_info", track_index=i)
        name = t.get("name")
        if name not in MIDI_EFFECTS:
            continue
        if t.get("devices"):
            print(f"{name}: already has {', '.join(d['name'] for d in t['devices'])}")
            continue
        if name not in uris:
            failed.append(f"{name} (not in the browser's MIDI Effects: {', '.join(sorted(uris))})")
            continue
        live.call("load_browser_item", track_index=i, item_uri=uris[name])
        now = live.call("get_track_info", track_index=i).get("devices", [])
        print(f"{name}: {', '.join(d['name'] + ' (' + d.get('class_name', '?') + ')' for d in now) or 'nothing loaded'}")
        if not now:
            failed.append(name)
    for f in failed:
        print(f"not loaded: {f}", file=sys.stderr)
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("-o", "--output", required=True)
    w.add_argument("--source", default=SOURCE, help="a set Live saved with the probe and a MIDI track")
    sub.add_parser("load")
    a = ap.parse_args(argv)
    return {"write": cmd_write, "load": cmd_load}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
