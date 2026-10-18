# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Writes the MIDI effects' measurement set and reads back what Live recorded from it.

    python midi_set.py check [measurements/30.*/runs.py ...]       # every run, every value
    python midi_set.py build -o measurements/midi-effects/midi-effects.als [runs.py ...]
    python live_check.py open measurements/midi-effects/midi-effects.als
    python midi_set.py verify measurements/midi-effects/midi-effects.cases.json
    # in Live: record the Arrangement from 1.1.1 to the end marker (the UI step), then
    python midi_set.py read measurements/midi-effects/midi-effects.cases.json

A MIDI effect is observed by the MIDI it emits (live-12/midi-effects/common.md › Measurement
plan, way 1). Each case gets two MIDI tracks:

- **the source**, named `<run> <case id>`: an Arrangement clip with the run's input notes (and
  the clip's scale, for Use Current Scale) and the device with the case's values, then no
  instrument;
- **the recorder**, named `rec <run> <case id>`: no devices, its MIDI input taken from the
  source track after its devices (`--route`), armed, monitoring off.

One Arrangement recording over the whole set then records every device's output at once, and
`read` takes the recorded clips' notes through the AbletonMCP Remote Script
(`get_session_snapshot`) into `<set>.recorded.json` and one `live/<run>.json` per run in the
device's folder: per case, the input notes and the output notes, start and length in beats from
the start of the song. Every input clip starts at bar 2 (`LEAD`), so nothing falls on the first
instant of the take; the set ends `TAIL` beats after the longest clip.

**Runs** live in each MIDI effect folder's `runs.py` (`measurements/30.NN-name/`), with
`DEVICE` (the display name) and `RUNS`, a list of dicts:

    {"name": "pitch-transpose",            # unique; starts with the device's slug
     "plan": "2",                          # the step(s) of the note's Measurement plan
     "question": "output pitch per input pitch for Pitch 0, +1, +12 ...",
     "clip": {"length": 132, "notes": [[pitch, start, length, velocity, release velocity], ...],
              "scale": ["C", "Major"]},    # optional; omitted = the clip's Scale Mode off
     "base": {"Range": 127},               # every case, and the run's `default`, has these
     "cases": [["plus-1", {"Pitch": 1}],
               ["held", {"Pitch": 0}, {"automation": {"Pitch": [[0, 0], [2, 5]]},
                                       "clip": {...}}], ...]}

Times are in beats from the clip's start; a note's release velocity is optional (64). An extra
`"copy": n` gives a case its own track even when another case is stored the same (a second
instance of a random device). Value
specs are make_als.py's. `automation` writes an Arrangement envelope for a parameter: the first
point holds from before the song's start, each later one is a step at its beat. Every run also
gets a `bypass` case (Device On off: the input as Live passes it, the reference for timing) and
a `default` case (the base alone). Cases stored identically (the device, the clip and the
automation all the same) share one track pair.

The source and recorder tracks are copies of a MIDI track Live saved (`measurements/
populate-midi-12.4.6.als`), and the clip a copy of the MIDI clip it saved in its Groove Pool.
How Live stores a track's MIDI input from another track was not in any saved set when this was
written: `--route` is a format string for its `Target` (`{id}` is the source track's id), and the
`route-check` tracks at the top try the other candidates on one known source (Pitch +12), so the
first recording shows which one Live takes.
"""

import argparse
import copy
import importlib.util
import json
import os
import sys

import als
import live_check
import make_als

ROOT = make_als.ROOT
MEAS = os.path.join(ROOT, "measurements")
DEFAULTS = {
    "dump": os.path.join(MEAS, "dump-midi-12.4.6.json"),
    "devices": os.path.join(MEAS, "populate-midi-12.4.6.als"),
    "template": os.path.join(MEAS, "populate-midi-12.4.6.als"),
    "track": "Arpeggiator",
    "map": make_als.DEFAULTS["map"],
}
LEAD = 4.0   # beats before every input clip
TAIL = 16.0  # beats after the longest clip, for notes the devices hold or delay
ROUTE = "MidiIn/Track.{id}/TrackOut"
ROUTE_CANDIDATES = ["MidiIn/Track.{id}/TrackOut", "MidiIn/Track.{id}/PostFxOut",
                    "MidiIn/Track.{id}/PreFxOut", "MidiIn/Track.{id}/PostMixer"]
MONITOR_OFF = "2"  # MonitoringEnum: 0 In, 1 Auto, 2 Off
BEFORE_SONG = "-63072000"  # the time of an envelope's first point, which holds from the start
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
# the clip's Scale Name chooser: the Scale device's list without its first entry ("User")
CLIP_SCALES = ["Major", "Minor", "Dorian", "Mixolydian", "Lydian", "Phrygian", "Locrian",
               "Whole Tone", "Half-whole Dim.", "Whole-half Dim.", "Minor Blues",
               "Minor Pentatonic", "Major Pentatonic", "Harmonic Minor", "Harmonic Major",
               "Dorian #4", "Phrygian Dominant", "Melodic Minor", "Lydian Augmented",
               "Lydian Dominant", "Super Locrian", "8-Tone Spanish", "Bhairav",
               "Hungarian Minor", "Hirajoshi", "In-Sen", "Iwato", "Kumoi", "Pelog Selisir",
               "Pelog Tembung", "Messiaen 3", "Messiaen 4", "Messiaen 5", "Messiaen 6",
               "Messiaen 7"]


# ---------------------------------------------------------------- runs

def load_runs(paths=None):
    """[(run, device display name, device folder)] from the MIDI effects' runs.py files."""
    if not paths:
        paths = sorted(os.path.join(MEAS, d, "runs.py") for d in os.listdir(MEAS)
                       if d.startswith("30.") and os.path.exists(os.path.join(MEAS, d, "runs.py")))
    out, seen = [], set()
    for path in paths:
        spec = importlib.util.spec_from_file_location(f"midi_runs_{len(seen)}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for r in mod.RUNS:
            if r["name"] in seen:
                raise SystemExit(f"{path}: run {r['name']} is defined twice")
            seen.add(r["name"])
            out.append((r, mod.DEVICE, os.path.dirname(os.path.abspath(path))))
    return out


def run_cases(run):
    """[(case id, params, extras)]: bypass, default, then the run's own."""
    base = run.get("base") or {}
    out = [("bypass", dict(base, **{"Device On": {"item": "Off"}}), {}),
           ("default", dict(base), {})]
    for c in run["cases"]:
        cid, params = c[0], c[1]
        extras = c[2] if len(c) > 2 else {}
        out.append((cid, dict(base, **params), extras))
    return out


def norm_notes(notes):
    """Notes as [pitch, start, length, velocity, release velocity], sorted by start and pitch."""
    out = []
    for n in notes:
        p, s, d, v = int(n[0]), float(n[1]), float(n[2]), float(n[3])
        off = float(n[4]) if len(n) > 4 else 64.0
        if not 0 <= p <= 127 or d <= 0 or not 1 <= v <= 127 or not 0 <= off <= 127 or s < 0:
            raise ValueError(f"bad note {n}")
        out.append([p, s, d, v, off])
    return sorted(out, key=lambda n: (n[1], n[0]))


def norm_clip(clip):
    notes = norm_notes(clip["notes"])
    end = max((n[1] + n[2] for n in notes), default=0.0)
    length = float(clip.get("length") or end)
    if length < end:
        raise ValueError(f"clip length {length} is shorter than its notes ({end})")
    scale = clip.get("scale")
    if scale is not None:
        root, name = scale
        if root not in NOTE_NAMES or name not in CLIP_SCALES:
            raise ValueError(f"bad scale {scale}")
        scale = [root, name]
    return {"length": length, "notes": notes, "scale": scale}


# ---------------------------------------------------------------- the set

def clip_skeleton(root):
    """The MIDI clip Live saved in the template's Groove Pool, as a skeleton for input clips."""
    e = root.find("LiveSet/GroovePool/Grooves/Groove/Clip/Value/MidiClip")
    if e is None:
        raise SystemExit("the template set has no MIDI clip in its Groove Pool to copy")
    return e


def make_clip(skeleton, clip, start, name):
    c = copy.deepcopy(skeleton)
    length = clip["length"]
    c.set("Id", "0")
    c.set("Time", repr(start))
    c.find("CurrentStart").set("Value", repr(start))
    c.find("CurrentEnd").set("Value", repr(start + length))
    loop = c.find("Loop")
    for tag, v in (("LoopStart", 0.0), ("LoopEnd", length), ("StartRelative", 0.0),
                   ("OutMarker", length), ("HiddenLoopStart", 0.0), ("HiddenLoopEnd", length)):
        loop.find(tag).set("Value", repr(v))
    loop.find("LoopOn").set("Value", "false")
    c.find("Name").set("Value", name)
    c.find("ScrollerTimePreserver/LeftTime").set("Value", "0")
    c.find("ScrollerTimePreserver/RightTime").set("Value", repr(length))
    c.find("TimeSelection/AnchorTime").set("Value", "0")
    c.find("TimeSelection/OtherTime").set("Value", "0")
    scale = clip["scale"]
    c.find("IsInKey").set("Value", "true" if scale else "false")
    c.find("ScaleInformation/Root").set("Value", str(NOTE_NAMES.index(scale[0]) if scale else 0))
    c.find("ScaleInformation/Name").set("Value", str(CLIP_SCALES.index(scale[1]) if scale else 0))
    tracks = c.find("Notes/KeyTracks")
    for k in list(tracks):
        tracks.remove(k)
    note_id = 1
    for i, pitch in enumerate(sorted({n[0] for n in clip["notes"]})):
        kt = als.ET.SubElement(tracks, "KeyTrack", Id=str(i))
        evs = als.ET.SubElement(kt, "Notes")
        for p, s, d, v, off in clip["notes"]:
            if p != pitch:
                continue
            als.ET.SubElement(evs, "MidiNoteEvent", Time=repr(s), Duration=repr(d),
                              Velocity=format(v, "g"), OffVelocity=format(off, "g"),
                              NoteId=str(note_id))
            note_id += 1
        als.ET.SubElement(kt, "MidiKey", Value=str(pitch))
    c.find("Notes/NoteIdGenerator/NextId").set("Value", str(note_id))
    return c


def arrangement_events(track):
    return track.find("DeviceChain/MainSequencer/ClipTimeable/ArrangerAutomation/Events")


def add_envelope(track, device, element, kind, points):
    """An Arrangement envelope on the device parameter `element`: [(beat or None, stored)],
    None for the value before the song starts."""
    target = als.parameter(device, element).find("AutomationTarget").get("Id")
    envs = track.find("AutomationEnvelopes/Envelopes")
    env = als.ET.SubElement(envs, "AutomationEnvelope", Id=str(len(envs)))
    als.ET.SubElement(als.ET.SubElement(env, "EnvelopeTarget"), "PointeeId", Value=target)
    auto = als.ET.SubElement(env, "Automation")
    events = als.ET.SubElement(auto, "Events")
    tag = {"bool": "BoolEvent", "int": "EnumEvent"}.get(kind, "FloatEvent")
    # a float envelope ramps between its points, so each step repeats the value before it at
    # the same time; a value from before the song otherwise ramps towards the first step
    steps = []
    for t, stored in points:
        if t is not None and tag == "FloatEvent" and steps:
            steps.append((t, steps[-1][1]))
        steps.append((t, stored))
    for i, (t, stored) in enumerate(steps):
        als.ET.SubElement(events, tag, Id=str(i + 1), Time=BEFORE_SONG if t is None else repr(t),
                          Value=stored)
    view = als.ET.SubElement(auto, "AutomationTransformViewState")
    als.ET.SubElement(view, "IsTransformPending", Value="false")
    als.ET.SubElement(view, "TimeAndValueTransforms")


def make_recorder(root, template, name, source, ids, route):
    rec = als.add_track(root, template, name, [], ids)
    target = rec.find("DeviceChain/MidiInputRouting/Target")
    target.set("Value", route.format(id=source.get("Id")))
    rec.find("DeviceChain/MidiInputRouting/UpperDisplayString").set("Value", als.track_name(source))
    rec.find("DeviceChain/MidiInputRouting/LowerDisplayString").set("Value", "")
    seq = rec.find("DeviceChain/MainSequencer")
    seq.find("Recorder/IsArmed").set("Value", "true")
    seq.find("MonitoringEnum").set("Value", MONITOR_OFF)
    return rec


class Builder:
    def __init__(self, a):
        self.dump = make_als.load_json(a.dump)
        self.devices_root = als.read_set(a.devices)
        self.amap = make_als.load_json(a.map)["devices"]
        self.root = als.read_set(a.template)
        self.template = als.find_track(self.root, a.track)
        self.skeleton = copy.deepcopy(clip_skeleton(self.root))
        als.remove_returns(self.root)
        als.clear_tracks(self.root)
        self.ids = als.Ids(self.root)
        self.route = a.route
        self.shared = {}
        self.cases = []
        self.end = 0.0

    def device(self, name, params):
        """(device element, {param: record}, [errors]) for a case's values."""
        dd = make_als.dump_device(self.dump, name)
        cls = dd["class_name"]
        if cls not in self.amap:
            raise SystemExit(f"{cls} is not in the map yet; calibrate it first (tools/README.md › 2b)")
        dparams, mparams = make_als.dump_params(dd), self.amap[cls]["params"]
        dev = copy.deepcopy(make_als.source_device(self.devices_root, dd))
        recs, errors = {}, []
        for pname, vspec in params.items():
            item, dp = mparams.get(pname), dparams.get(pname)
            if item is None or dp is None:
                errors.append(f"{pname}: not in the map" if dp else f"no parameter {pname}")
                continue
            el = als.parameter(dev, item["element"])
            try:
                v, text = make_als.stored_value(item, dp, vspec, als.controller_range(el))
            except ValueError as e:
                errors.append(f"{pname}: {e}")
                continue
            als.set_manual(el, text)
            recs[pname] = {"value": v, "element": item["element"], "stored": text}
            if isinstance(vspec, dict) and "display" in vspec and dp.get("samples"):
                recs[pname]["tol"] = 1.0 / (len(dp["samples"]) - 1)
        return cls, dev, recs, errors, (dparams, mparams)

    def automation(self, dev, maps, auto):
        """{param: [[beat, stored], ...]} and the envelope specs, from a case's automation."""
        dparams, mparams = maps
        out, envs, errors = {}, [], []
        for pname, points in (auto or {}).items():
            item, dp = mparams.get(pname), dparams.get(pname)
            if item is None or dp is None:
                errors.append(f"automation {pname}: no such parameter in the map")
                continue
            el = als.parameter(dev, item["element"])
            pts, first = [], None
            for i, (t, vspec) in enumerate(points):
                try:
                    v, text = make_als.stored_value(item, dp, vspec, als.controller_range(el))
                except ValueError as e:
                    errors.append(f"automation {pname} at {t}: {e}")
                    continue
                first = v if i == 0 else first
                pts.append([None if i == 0 else LEAD + float(t), text])
            if pts:
                # the parameter's own value is the envelope's first point, which verify checks
                als.set_manual(el, pts[0][1])
                out[pname] = {"element": item["element"], "points": pts, "value": first}
                envs.append((item["element"], item["kind"], pts))
        return out, envs, errors

    def add_case(self, run, device_name, cid, params, extras, folder=None):
        clip = norm_clip(extras.get("clip") or run["clip"])
        cls, dev, recs, errors, maps = self.device(device_name, params)
        auto, envs, aerr = self.automation(dev, maps, extras.get("automation"))
        errors += aerr
        for pname, env in auto.items():
            recs[pname] = {"value": env["value"], "element": env["element"],
                           "stored": env["points"][0][1], "automated": True}
        rec = {"id": f"{run['name']} {cid}", "run": run["name"], "case": cid, "device": cls,
               "folder": os.path.relpath(folder, ROOT) if folder else None,
               "params": recs, "automation": auto, "errors": errors,
               "clip": {"start": LEAD, "length": clip["length"], "scale": clip["scale"],
                        "notes": [[p, LEAD + s, d, v, off] for p, s, d, v, off in clip["notes"]]}}
        # `copy` keeps a second, identical instance on its own track (random generators)
        key = json.dumps([cls, [als.manual(p) for _, p in als.parameters(dev)], clip, auto,
                          extras.get("copy")])
        if key in self.shared:
            rec["track"], rec["recorder"] = self.shared[key]
        else:
            src = als.add_track(self.root, self.template, rec["id"], [dev], self.ids)
            arrangement_events(src).append(make_clip(self.skeleton, clip, LEAD, rec["id"]))
            placed = als.devices_holder(src)[0]
            for element, kind, pts in envs:
                add_envelope(src, placed, element, kind, pts)
            make_recorder(self.root, self.template, "rec " + rec["id"], src, self.ids, self.route)
            rec["track"], rec["recorder"] = self.shared[key] = (rec["id"], "rec " + rec["id"])
        self.end = max(self.end, LEAD + clip["length"])
        self.cases.append(rec)
        return rec

    def add_route_check(self):
        """One Pitch +12 source on a single C3 and a recorder per routing candidate."""
        clip = norm_clip({"length": 4, "notes": [[60, 0, 1, 100], [64, 1, 1, 100], [67, 2, 1, 100]]})
        cls, dev, recs, errors, _ = self.device("Pitch", {"Pitch": 12})
        src = als.add_track(self.root, self.template, "route-check source", [dev], self.ids)
        arrangement_events(src).append(make_clip(self.skeleton, clip, LEAD, "route-check"))
        out = []
        for i, fmt in enumerate(ROUTE_CANDIDATES):
            name = f"rec route-check {i + 1}"
            make_recorder(self.root, self.template, name, src, self.ids, fmt)
            out.append({"recorder": name, "route": fmt})
        return {"source": "route-check source", "device": cls, "params": recs,
                "input": [[p, LEAD + s, d, v, off] for p, s, d, v, off in clip["notes"]],
                "expect": "the input 12 semitones up", "recorders": out}

    def finish(self, path, route_check):
        set_loop(self.root, self.end + TAIL)
        make_als.write_out(self.root, self.ids, path)
        side = os.path.splitext(path)[0] + ".cases.json"
        out = {"set": os.path.basename(path), "generated_by": "midi_set.py", "route": self.route,
               "lead_beats": LEAD, "end_beats": self.end + TAIL, "tempo": make_als.set_tempo(self.root),
               "route_check": route_check, "cases": self.cases}
        with open(side, "w") as f:
            json.dump(out, f, indent=1)
        return side


def set_loop(root, end):
    """The Arrangement loop over the whole take, so the loop brace marks where to stop recording."""
    loop = root.find("LiveSet/Transport")
    if loop is None:
        return
    for tag, v in (("LoopStart", 0.0), ("LoopLength", end)):
        e = loop.find(tag)
        if e is not None:
            e.set("Value", repr(v))
    on = loop.find("LoopOn")
    if on is not None:
        on.set("Value", "false")


def build_all(a, runs):
    b = Builder(a)
    rc = b.add_route_check() if not a.no_route_check else None
    for run, device, folder in runs:
        for cid, params, extras in run_cases(run):
            try:
                b.add_case(run, device, cid, params, extras, folder)
            except ValueError as e:
                b.cases.append({"id": f"{run['name']} {cid}", "errors": [str(e)]})
    return b, rc


def selected(a):
    runs = load_runs(a.runs or None)
    if a.only:
        want = set(a.only)
        runs = [r for r in runs if r[0]["name"] in want]
        missing = want - {r[0]["name"] for r in runs}
        if missing:
            raise SystemExit(f"no such runs: {', '.join(sorted(missing))}")
    return runs


def report(b):
    problems = [(c["id"], e) for c in b.cases for e in c.get("errors", [])]
    for cid, e in problems:
        print(f"  {cid}: {e}", file=sys.stderr)
    pairs = len({c.get("track") for c in b.cases if c.get("track")})
    return problems, pairs


def cmd_check(a):
    a.no_route_check = False
    runs = selected(a)
    b, _ = build_all(a, runs)
    problems, pairs = report(b)
    print(f"{len(runs)} runs, {len(b.cases)} cases on {pairs} track pairs, "
          f"take {b.end + TAIL:.0f} beats; {len(problems)} problems")
    return 1 if problems else 0


def cmd_build(a):
    runs = selected(a)
    b, rc = build_all(a, runs)
    problems, pairs = report(b)
    side = b.finish(a.output, rc)
    tempo = make_als.set_tempo(b.root)
    print(f"wrote {a.output}: {len(runs)} runs, {len(b.cases)} cases on {pairs} track pairs "
          f"({2 * pairs + (5 if rc else 0)} tracks), take 1.1.1 to beat {b.end + TAIL:.0f} "
          f"({(b.end + TAIL) * 60 / tempo:.0f} s at {tempo:g} BPM); and {side}"
          + (f"; {len(problems)} problems" if problems else ""))
    return 1 if problems else 0


# ---------------------------------------------------------------- after Live

def cmd_verify(a):
    """live_check.py verify on the source tracks, then the recorders' arm state."""
    va = argparse.Namespace(cases=a.cases, read=None, dump=a.dump, tol=0.002, output=a.output)
    status = live_check.cmd_verify(va)
    spec = make_als.load_json(a.cases)
    live = live_check.Live()
    info = live.call("get_session_info")
    armed = {}
    for i in range(int(info["track_count"])):
        t = live.call("get_track_info", track_index=i)
        armed[t["name"]] = t.get("arm")
    want = {c["recorder"] for c in spec["cases"] if c.get("recorder")}
    if spec.get("route_check"):
        want |= {r["recorder"] for r in spec["route_check"]["recorders"]}
    bad = sorted(n for n in want if armed.get(n) is not True)
    for n in bad:
        print(f"{n}: {'no such track' if n not in armed else 'not armed'}")
    print(f"{len(want)} recorders checked, {len(bad)} not armed")
    return 1 if bad or status else 0


def recorded_notes(track):
    """Every note of a track's Arrangement clips, start in beats from the song's start."""
    out = []
    for clip in track.get("arrangement_clips", []):
        for n in clip.get("notes", []):
            if n.get("mute"):
                continue
            out.append([n["pitch"], round(clip["start_time"] + n["start_time"], 6),
                        round(n["duration"], 6), n["velocity"], n.get("release_velocity")])
    return sorted(out, key=lambda n: (n[1], n[0]))


def cmd_read(a):
    spec = make_als.load_json(a.cases)
    snap = live_check.Live(timeout=300).call("get_session_snapshot", include_notes=True,
                                             include_params=False)
    tracks = {t["name"]: t for t in snap["tracks"]}
    out = {"set": spec["set"], "tempo": snap.get("session", {}).get("tempo"), "cases": []}
    rc = spec.get("route_check")
    if rc:
        out["route_check"] = []
        for r in rc["recorders"]:
            notes = recorded_notes(tracks.get(r["recorder"], {}))
            out["route_check"].append(dict(r, notes=notes))
            print(f"route check {r['route']}: {len(notes)} notes "
                  f"({', '.join(str(n[0]) for n in notes[:6])})")
    empty = 0
    by_run = {}
    for c in spec["cases"]:
        if not c.get("recorder"):
            continue
        t = tracks.get(c["recorder"])
        notes = recorded_notes(t) if t else None
        empty += not notes
        row = {"id": c["id"], "run": c["run"], "case": c["case"], "track": c["track"],
               "params": {k: v.get("live", {"value": v["value"]}) for k, v in c["params"].items()},
               "automation": c.get("automation") or {}, "input": c["clip"]["notes"],
               "scale": c["clip"]["scale"], "output": notes}
        out["cases"].append(row)
        by_run.setdefault((c["run"], c.get("folder")), []).append(row)
    path = a.output or os.path.splitext(a.cases)[0].replace(".cases", "") + ".recorded.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    for (run, folder), rows in by_run.items():
        if not folder:
            continue
        d = os.path.join(ROOT, folder, "live")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{run}.json"), "w") as f:
            json.dump({"set": spec["set"], "run": run, "lead_beats": spec["lead_beats"],
                       "tempo": out["tempo"], "cases": rows}, f, indent=1)
    print(f"wrote {path} and {len(by_run)} runs' live/<run>.json: {len(out['cases'])} cases, "
          f"{empty} with no recorded notes")
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--dump", default=DEFAULTS["dump"])
        p.add_argument("--devices", default=DEFAULTS["devices"])
        p.add_argument("--template", default=DEFAULTS["template"],
                       help="a set Live saved with a MIDI track and a MIDI clip in its Groove Pool")
        p.add_argument("--track", default=DEFAULTS["track"], help="that MIDI track's name")
        p.add_argument("--map", default=DEFAULTS["map"])
        p.add_argument("--route", default=ROUTE, help="the recorders' MIDI input Target; {id} = source track id")
        p.add_argument("--only", action="append", help="build only this run (repeatable)")
        p.add_argument("runs", nargs="*", help="runs.py files (default: every measurements/30.*/runs.py)")

    c = sub.add_parser("check")
    common(c)
    b = sub.add_parser("build")
    common(b)
    b.add_argument("-o", "--output", required=True)
    b.add_argument("--no-route-check", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("cases")
    v.add_argument("--dump", default=DEFAULTS["dump"])
    v.add_argument("-o", "--output")
    r = sub.add_parser("read")
    r.add_argument("cases")
    r.add_argument("-o", "--output")
    a = ap.parse_args(argv)
    return {"check": cmd_check, "build": cmd_build, "verify": cmd_verify, "read": cmd_read}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
