# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Runs many devices' behaviour runs as one Live Set: one build, one export, one analysis.

    python batch.py check   [measurements/29.*/runs.py ...]     # every run, every device
    python batch.py build   measurements/top100/selection.json  # cases files, the set, its .cases.json
    python batch.py analyse measurements/top100/selection.json --export measurements/top100/export
    python batch.py summary measurements/top100/selection.json [run ...]   # key figures per case

**Runs.** Each device folder (`measurements/29.NN-name/`) can hold a `runs.py` with
`DEVICE` (its display name) and `RUNS`, a list of dicts:

    {"name": "compressor-ratio",          # unique over all devices; starts with the device's slug
     "plan": "2",                         # the step(s) of the note's Measurement plan it answers
     "question": "slope above the threshold for Ratio 2 to inf, hard knee, Peak",
     "read": ["static"],                  # which parts of analyse.py's result answer it
     "probe": "gap2",                     # a key of the selection's "probes" (default gap2)
     "base": {"Model": {"item": "Peak"}}, # every case, and the run's `default`, has these
     "cases": [["ratio-2", {"Ratio": {"display": 2}}], ...]}

Value specs are make_als.py's (`{"norm": x}`, `{"display": x}` in base units, `{"item": "Peak"}`,
a bare API value, `{"stored": x}`). Every run gets a `bypass` case (Device On off) and a `default`
case (the base alone) in front of its own. `check` loads every `runs.py` and works out every
value against the dump and the map, as `build` would, so a wrong name or an impossible value
shows before Live is involved.

**Selection.** `selection.json` names the set, the probes and the runs, ranked:

    {"name": "top100",
     "probes": {"gap2": "measurements/probe.wav", "gap10": "measurements/29.32-reverb/probe-gap10/probe.wav"},
     "runs": ["compressor-ratio", ...]}

`build` writes each run's cases file beside its `runs.py` (`<run>.json`, with its probe), then one
set from all of them, ordered by probe so each probe's tracks are together, with
`make_als.py build --share`: every run's `bypass` of a device, and any case another run already
has, plays on one track, and is rendered and analysed once. Each track's clip points at the one
probe file of its group, so the set copies no audio.

**Export.** Open the set, check it (`live_check.py verify <set>.cases.json -o <set>.verified.json`),
then export into `--export`: either each probe's tracks on their own, under the name `<set name>`
for the first probe and `<set name>-<probe>` for the others (select that group's tracks, Rendered
Track Selected Tracks Only, the probe's length), or every track at once under `<set name>` at the
longest probe's length, and `analyse --trim` cuts each render back to its own probe's length.

**Analyse.** For each probe group, the bypass renders give the export's offset against the probe
(Live has exported a whole set 40 ms early); every track of the group is analysed with that
offset into its device's `live/` as `<track>.json` and so on. `<set>.analysis.json` records the
offsets and, per run and case, the result file.
"""

import argparse
import importlib.util
import json
import math
import os
import sys
from collections import Counter

import als
import analyse
import make_als
from wavio import read_wav, write_wav

ROOT = make_als.ROOT
MEAS = os.path.join(ROOT, "measurements")


def load_runs(paths=None):
    """{run name: (run dict, device display name, device folder)} from the runs.py files."""
    if not paths:
        # the audio effects' folders; the MIDI effects' runs (30.*) go through midi_set.py
        paths = sorted(os.path.join(MEAS, d, "runs.py") for d in os.listdir(MEAS)
                       if d.startswith("29.") and os.path.exists(os.path.join(MEAS, d, "runs.py")))
    out = {}
    for path in paths:
        spec = importlib.util.spec_from_file_location(f"runs_{len(out)}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for r in mod.RUNS:
            if r["name"] in out:
                raise SystemExit(f"{path}: run {r['name']} is also in {out[r['name']][2]}")
            out[r["name"]] = (r, mod.DEVICE, os.path.dirname(os.path.abspath(path)))
    return out


def run_cases(r):
    """The run's cases, with `bypass` and `default` in front."""
    base = dict(r.get("base") or {})
    out = [{"id": "bypass", "params": {"Device On": 0}}, {"id": "default", "params": dict(base)}]
    for cid, params in r["cases"]:
        p = dict(base)
        p.update(params)
        out.append({"id": cid, "params": p})
    ids = [c["id"] for c in out]
    dup = [i for i, n in Counter(ids).items() if n > 1]
    if dup:
        raise ValueError(f"duplicate case ids {dup}")
    return out


def check_run(r, device, dump, amap, devices_root):
    """Problems with a run's values, worked out as make_als.py build would."""
    problems = []
    try:
        cs = run_cases(r)
    except ValueError as e:
        return [str(e)]
    dd = make_als.dump_device(dump, device)
    cls = dd["class_name"]
    if cls not in amap:
        return [f"{cls} is not in the map"]
    dparams = make_als.dump_params(dd)
    mparams = amap[cls]["params"]
    dev = make_als.source_device(devices_root, dd)
    for c in cs:
        for name, vspec in c["params"].items():
            item, dp = mparams.get(name), dparams.get(name)
            if dp is None:
                problems.append(f"{c['id']}: no parameter {name!r}")
                continue
            if item is None:
                problems.append(f"{c['id']}: {name} is not in the map")
                continue
            try:
                make_als.stored_value(item, dp, vspec, als.controller_range(als.parameter(dev, item["element"])))
            except ValueError as e:
                problems.append(f"{c['id']}: {name}: {e}")
    for k in ("name", "question", "cases"):
        if not r.get(k):
            problems.append(f"no {k}")
    return problems


def cmd_check(a):
    runs = load_runs(a.runs)
    dump = make_als.load_json(make_als.DEFAULTS["dump"])
    amap = make_als.load_json(make_als.DEFAULTS["map"])["devices"]
    devices_root = als.read_set(make_als.DEFAULTS["devices"])
    bad = 0
    tracks = 0
    for name, (r, device, folder) in runs.items():
        ps = check_run(r, device, dump, amap, devices_root)
        n = len(r["cases"]) + 2
        tracks += n
        print(f"{'FAIL' if ps else 'ok  '} {name:44} {device:24} {n:3} cases")
        for p in ps:
            print(f"       {p}")
        bad += bool(ps)
    print(f"{len(runs)} runs, {tracks} cases, {bad} with problems")
    return 1 if bad else 0


def selection(path):
    sel = make_als.load_json(path)
    runs = load_runs()
    missing = [n for n in sel["runs"] if n not in runs]
    if missing:
        raise SystemExit(f"{path}: no runs.py has {', '.join(missing)}")
    if len(set(sel["runs"])) != len(sel["runs"]):
        raise SystemExit(f"{path}: a run is listed twice")
    probes = list(sel["probes"])
    for n in sel["runs"]:
        if runs[n][0].get("probe", probes[0]) not in sel["probes"]:
            raise SystemExit(f"{n}: probe {runs[n][0]['probe']} is not in the selection")
    return sel, runs, probes


def set_path(sel_path, sel):
    return os.path.join(os.path.dirname(os.path.abspath(sel_path)), sel["name"] + ".als")


def cmd_build(a):
    sel, runs, probes = selection(a.selection)
    files = []
    for n in sorted(sel["runs"], key=lambda n: probes.index(runs[n][0].get("probe", probes[0]))):
        r, device, folder = runs[n]
        spec = {"device": device, "parameter": n, "question": r["question"], "plan": r.get("plan"),
                "read": r.get("read"), "probe": sel["probes"][r.get("probe", probes[0])],
                "cases": run_cases(r)}
        path = os.path.join(folder, n + ".json")
        with open(path, "w") as f:
            f.write(json.dumps(spec, indent=1) + "\n")
        files.append(path)
    out = a.output or set_path(a.selection, sel)
    first = os.path.join(ROOT, sel["probes"][probes[0]])
    return make_als.main(["build", *files, "-o", out, "--share", "--probe", first])


def file_name(track):
    """A track's name as Live writes it in an export's file name ("/" becomes "_"); the
    analysis files use it too."""
    return track.replace("/", "_")


def export_name(sel, probes, probe_key):
    return sel["name"] if probe_key == probes[0] else f"{sel['name']}-{probe_key}"


def cmd_analyse(a):
    sel, runs, probes = selection(a.selection)
    setp = set_path(a.selection, sel)
    spec = make_als.load_json(os.path.splitext(setp)[0] + ".cases.json")
    folder_of = {n: runs[n][2] for n in sel["runs"]}
    key_of = {os.path.normpath(p): k for k, p in sel["probes"].items()}
    groups = {}
    for c in spec["cases"]:
        groups.setdefault(key_of[os.path.normpath(c["probe"])], []).append(c)
    record = {"set": os.path.basename(setp), "groups": {}, "runs": {}}
    failed = 0
    for key, cs in groups.items():
        probe_wav = os.path.join(ROOT, sel["probes"][key])
        manifest = make_als.load_json(os.path.splitext(probe_wav)[0] + ".json")
        prate, probe = read_wav(probe_wav)
        name = export_name(sel, probes, key)

        def wav(track):
            # its own export, or one export of every track at the longest probe's length
            track = file_name(track)
            for n in (name, sel["name"]):
                p = os.path.join(a.export, f"{n} {track}.wav")
                if os.path.exists(p):
                    return p
            return os.path.join(a.export, f"{name} {track}.wav")

        # the export's offset, from every bypass render of the group
        offsets = {}
        for c in cs:
            if c["case"] == "bypass" and c["track"] == c["id"] and os.path.exists(wav(c["track"])):
                rate, audio = read_wav(wav(c["track"]))
                offsets[c["track"]] = analyse.find_latency(probe, audio[:len(probe)], rate)
        if not offsets:
            raise SystemExit(f"no bypass render of {key} in {a.export} (looked for '{name} <track>.wav')")
        offset, votes = Counter(offsets.values()).most_common(1)[0]
        odd = {t: o for t, o in offsets.items() if o != offset}
        record["groups"][key] = {"export": name, "offset_samples": offset, "bypass_renders": len(offsets),
                                 "bypass_disagreeing": odd}
        print(f"{key}: export '{name}', offset {offset} samples from {votes} of {len(offsets)} bypass renders"
              + (f"; disagreeing: {odd}" if odd else ""))
        done = set()
        for c in cs:
            out_dir = os.path.join(folder_of[c["run"]], "live")
            rel = os.path.relpath(os.path.join(folder_of[c["run"]], "live", file_name(c["track"]) + ".json"), ROOT)
            if c["track"] != c["id"]:
                # a shared track: analysed under the run that has it
                first = next(x for x in cs if x["id"] == c["track"])
                rel = os.path.relpath(os.path.join(folder_of[first["run"]], "live", file_name(c["track"]) + ".json"), ROOT)
            record["runs"].setdefault(c["run"], {})[c["case"]] = rel
            if c["track"] in done or c["track"] != c["id"]:
                continue
            done.add(c["track"])
            path = wav(c["track"])
            if not os.path.exists(path):
                print(f"missing {path}", file=sys.stderr)
                failed += 1
                continue
            if a.only and c["run"] not in a.only:
                continue
            rate, audio = read_wav(path)
            if a.trim and len(audio) > len(probe):
                # rendered past its probe's end (one export at the longest probe's length): cut to size
                audio = audio[:len(probe)]
                write_wav(path, rate, audio)
            try:
                result, extras = analyse.analyse(manifest, probe, audio, rate, str(offset))
            except (ValueError, KeyError) as e:
                print(f"{path}: {e}", file=sys.stderr)
                failed += 1
                continue
            result["source"] = os.path.relpath(path, ROOT)
            os.makedirs(out_dir, exist_ok=True)
            analyse.write_outputs(os.path.join(out_dir, file_name(c["track"])), result, extras, rate)
        print(f"{key}: {len(done)} renders analysed")
    out = os.path.splitext(setp)[0] + ".analysis.json"
    with open(out, "w") as f:
        json.dump(record, f, indent=1)
    print(f"wrote {out}" + (f"; {failed} failed" if failed else ""))
    return 1 if failed else 0


OCTAVES = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]


def nearest(centres, f):
    return min(range(len(centres)), key=lambda i: abs(math.log(centres[i] / f)))


def fmt(x, nd=2):
    return "-" if x is None else f"{x:.{nd}f}"


def summarise(res, read):
    """A few lines of the figures `read` names, from one analysis result."""
    lines = []
    read = read or ["impulse", "response", "static", "dynamics", "modulation", "stereo", "silence"]
    want = " ".join(read)
    if "impulse" in want or "ir" in want or "taps" in want:
        im = res["impulse"]
        taps = ", ".join(f"{t['time_ms']:.2f}ms {t['level_db']:.1f}dB" for t in im["taps"][:8])
        lines.append(f"impulse peak {fmt(im['peak_db'])} dB, rt60 {fmt(im['rt60_s'], 3)} s; taps {taps}")
    if "response" in want or "sweep" in want or "noise" in want:
        r = res["response"]
        idx = [nearest(r["centres_hz"], f) for f in OCTAVES]
        for label, k in (("sweep", "sweep_db"), ("noise", "noise_db")):
            if k.split("_")[0] in want or "response" in want:
                for ch, vals in zip("LR", r[k]):
                    lines.append(f"{label} {ch}: " + " ".join(f"{OCTAVES[j]:g}:{fmt(vals[i], 1)}"
                                                         for j, i in enumerate(idx)))
    if "static" in want:
        rows = res["static"]
        lines.append("static in->gain(L) thd%: " + " ".join(
            f"{r['in_db']:.0f}:{fmt(r['left_gain_db'])}/{fmt(r.get('left_thd_pct'), 1)}" for r in rows[::2]))
    if "dynamics" in want:
        d = res["dynamics"]
        lines.append(f"attack {fmt(d['attack']['from_db'])}->{fmt(d['attack']['to_db'])} dB t63 {d['attack']['t63_ms']} "
                     f"t90 {d['attack']['t90_ms']} ms; release {fmt(d['release']['from_db'])}->"
                     f"{fmt(d['release']['to_db'])} dB t63 {d['release']['t63_ms']} t90 {d['release']['t90_ms']} ms")
    if "modulation" in want:
        m = res["modulation"]
        for ch in ("left", "right"):
            x = m.get(ch) or {}
            am, fm = x.get("am") or {}, x.get("fm") or {}
            lines.append(f"mod {ch}: level {fmt(x.get('level_db'))} dB, AM {fmt(am.get('depth_db'))} dB at "
                         f"{fmt(am.get('rate_hz'), 3)} Hz, FM {fmt(fm.get('depth_cents'))} c at "
                         f"{fmt(fm.get('rate_hz'), 3)} Hz, mean {fmt(fm.get('mean_cents'))} c")
        if m.get("envelope_correlation") is not None:
            lines.append(f"mod L/R envelope correlation {fmt(m['envelope_correlation'])}")
    if "stereo" in want:
        st = res["stereo"]
        lines.append("stereo " + " ".join(f"{k.replace('_db', '')} {fmt(v, 1)}" for k, v in st.items()))
    if "silence" in want:
        lines.append(f"silence rms {res['silence']['rms_db']} peak {res['silence']['peak_db']} dB")
    return lines


def cmd_summary(a):
    sel, runs, probes = selection(a.selection)
    rec = make_als.load_json(os.path.splitext(set_path(a.selection, sel))[0] + ".analysis.json")
    for n in a.runs or sel["runs"]:
        r = runs[n][0]
        print(f"## {n} ({runs[n][1]}; plan {r.get('plan')}): {r['question']}")
        for case, rel in rec["runs"].get(n, {}).items():
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                print(f"  {case}: no result")
                continue
            print(f"  {case}:")
            for line in summarise(make_als.load_json(path), a.read or r.get("read")):
                print(f"    {line}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("runs", nargs="*", help="runs.py files (default: every device folder's)")
    b = sub.add_parser("build")
    b.add_argument("selection")
    b.add_argument("-o", "--output", help="default: <selection folder>/<name>.als")
    n = sub.add_parser("analyse")
    n.add_argument("selection")
    n.add_argument("--export", required=True, help="the folder Live exported into")
    n.add_argument("--only", nargs="*", help="analyse only these runs")
    n.add_argument("--trim", action="store_true",
                   help="cut each render to its probe's length in place (after one export of every track "
                        "at the longest probe's length)")
    m = sub.add_parser("summary")
    m.add_argument("selection")
    m.add_argument("runs", nargs="*", help="default: every run of the selection")
    m.add_argument("--read", nargs="*", help="parts to show instead of each run's `read`")
    a = ap.parse_args(argv)
    return {"check": cmd_check, "build": cmd_build, "analyse": cmd_analyse, "summary": cmd_summary}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
