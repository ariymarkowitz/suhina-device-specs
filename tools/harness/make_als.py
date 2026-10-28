# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Writes a Live Set with one track per test case, without Build cases or any clicking in Live.

    python make_als.py calibrate --device Compressor -o calib.als
    python live_check.py read -o calib.read.json            # with calib.als open in Live
    python make_als.py map calib.calibration.json calib.read.json
    python make_als.py build cases.json [cases.json ...] -o measure.als [--probe gap10] [--share]
    python live_check.py verify measure.cases.json          # with measure.als open in Live

A set holds each parameter as a stored value in its own units, under an element name that
often differs from the parameter's API name and in a different order (Compressor's Output is
`Gain`, EQ Eight's Adaptive Q comes last). So a device is first calibrated:

- `calibrate` writes a set with a `ref` track per device (its factory default) and one track per
  parameter element with only that element's stored value changed.
- Open it in Live and read every track's parameters through the AbletonMCP Remote Script
  (`live_check.py read`).
- `map` compares each track with its `ref`: the one API parameter that moved is the element's.
  From the stored and API values at the default and the changed value, and the dump's display
  text, it picks how an API value becomes a stored value (the same number; the same number as
  an integer; the display's number in Hz, s, ms, % / 100 or dB as linear gain; a straight line
  from the API range onto the element's controller range; an index), and writes it to the map
  file (`reference/als-map-12.4.6.json`).

`build` then writes any number of cases files (cases.py's format) into one set: a copy of the
template track per case, named `<run> <case id>` (run = the cases file's name), holding a fresh
copy of the device with the case's values. A cases file can name its own probe (`"probe"`), so
runs with different probes share a set; its tracks' clips play that file. With `--share`, cases
whose device is stored identically with the same probe (every run's `bypass`, a `default` that
another run also uses) get one track, named after the first such case. Beside the set it writes
`<set>.cases.json`: every case's device, the track it plays on (`track`) and the API value and
stored value it should have. `live_check.py verify` checks
those against Live, which is the test that the set means what it should.

Value specs are cases.py's (`norm`, `value` or a plain number, `item`, `display`) plus
`{"stored": x}`, which writes x as it is. A `display` value in base units (Hz, s, dB, %) is
converted exactly; a `norm` or `value` goes through the dump's sampled display curve
(65 points), so it lands within the display's rounding (three figures) of the target.

Two more kinds of case entry reach what a static parameter value cannot:

- **A stored element**, named `@<path>` (`"@Input_RoutingMode": 0`, `"@Oversampling": true`):
  an element of the device that is no API parameter (Roar's routing mode, the Hi-Quality
  switches, Vocoder's band count), written as it is into its `Value` (or its `Manual`). Live
  cannot report these, so `verify` does not check them; `<set>.cases.json` lists them under
  `elements`.
- **A side-chain key**: a stored element whose value is `"key:<name>"` (a
  probe name from probes.py, or a WAV path from the repository), such as
  `"@SideChain/RoutedInput/Routable/Target": "key:key-duck"`.
  The set gets one track per key file, named `key <file>`, playing it from the start like a
  probe (no device), and the element is written as that track's post-FX output
  (`AudioIn/Track.<id>/PostFxOut`, the form Live's own sets use). The device's side-chain
  switch is still its parameter (`"S/C On"`).
- **A MIDI key**: a stored element given `{"midi": {"notes": [[pitch, beat, length, velocity],
  ...], "length": beats, "name": "..."}, "out": "TrackOut"}`, for a device's MIDI side-chain
  (`"@MidiSideChain/RoutedInput/Routable/Target"`). The set gets a MIDI track per distinct clip
  (no instrument; the clip from beat 0, notes in midi_set.py's form), and the element is written
  as `MidiIn/Track.<id>/<out>`, the form midi_set.py found Live takes for a track's MIDI output.
- **An automation lane**, `{"auto": [[beat, spec], ...]}`: the parameter follows the points
  (each spec as above) through the song, as an arrangement envelope on the case's track.
  Between points a float glides linearly and a stepped value holds; two points at one beat
  make a jump. A point with a third item `[x1, y1, x2, y2]` bends the segment that starts at it
  (Bezier control points in share of time and share of the way; Live's own pair for a bend
  mirrors through the centre). The device stores the first point's value, which is what `verify` expects (Live
  shows the envelope's value at the start of the song). At 120 BPM a beat is 0.5 s of the probe.
"""

import argparse
import copy
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

import als
import probes
from wavio import read_wav

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROJECT_INFO = "Ableton Project Info"
DEFAULTS = {
    "dump": os.path.join(ROOT, "reference", "dump-12.4.6.json"),
    "devices": os.path.join(ROOT, "reference", "populate-12.4.6.als"),
    "template": os.path.join(HERE, "data", "template.als"),
    "track": None,
    "map": os.path.join(ROOT, "reference", "als-map-12.4.6.json"),
    "probe": "gap2",
}

# How an API value becomes a stored value, for continuous parameters, by the display's number
# in base units (Hz, s, dB, %, or the bare number). "same" uses the API value itself.
CONVERSIONS = {
    "base": lambda n: n,
    "ms": lambda n: n * 1000.0,
    "percent": lambda n: n / 100.0,
    "gain": lambda n: 10.0 ** (n / 20.0),
}
# the display unit (in base units) each conversion needs; "base" takes any
UNITS = {"ms": "s", "percent": "%", "gain": "dB"}
# "integer": the stored value is the API value, but Live truncates a stored fraction on loading
# (Corpus Transpose); "linear": the API range maps linearly onto the element's controller range
# (Saturator's Color Amt Low, -36 .. 36)
PREFERENCE = ["same", "base", "ms", "percent", "gain", "integer", "linear"]


# ---------------------------------------------------------------- display text

def parse_display(text):
    """(number in base units, unit, half of the last shown digit in base units), or None.
    Base units: Hz (from kHz), s (from ms), and the shown unit otherwise."""
    s = str(text).replace("−", "-").strip()
    m = re.match(r"^([+-]?)\s*inf\b\s*(.*)$", s, re.I)
    if m:
        return (-math.inf if m.group(1) == "-" else math.inf), m.group(2).strip(), 0.0
    m = re.match(r"^([+-]?\d+(?:\.(\d+))?)\s*(.*)$", s)
    if not m:
        return None
    n = float(m.group(1))
    half = 0.5 * 10.0 ** -(len(m.group(2)) if m.group(2) else 0)
    unit = m.group(3).strip()
    scale = {"khz": (1000.0, "Hz"), "ms": (0.001, "s")}.get(unit.lower())
    if scale:
        return n * scale[0], scale[1], half * scale[0]
    return n, unit, half


def keyed(names):
    """Unique keys for a device's parameter names: a repeated name gets ' #2', ' #3'."""
    seen = {}
    out = []
    for n in names:
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else f"{n} #{seen[n]}")
    return out


# ---------------------------------------------------------------- loading

def load_json(path):
    with open(path) as f:
        return json.load(f)


# Devices whose class the probe misreads, by the track the dump found them on: Live 12.4.6's
# API gave CC Control's class_name and class_display_name as "0" to the probe, where the Remote
# Script and the saved set give MidiCcControl.
CLASS_FIXES = {"CC Control": "MidiCcControl"}


def dump_device(dump, name):
    """The dump's entry for a device by class or display name, preferring the fresh copy that
    Populate put on a track named after it."""
    hits = []
    for d in dump["devices"]:
        fix = CLASS_FIXES.get(d.get("track"))
        if fix and d.get("class_name") == "0":
            d = dict(d, class_name=fix, class_display_name=d["track"])
        if name in (d.get("class_name"), d.get("class_display_name")):
            hits.append(d)
    if not hits:
        raise SystemExit(f"no device {name!r} in the dump")
    fresh = [d for d in hits if d.get("track") == d.get("class_display_name")]
    return (fresh or hits)[0]


def dump_params(device):
    return dict(zip(keyed([p["name"] for p in device["parameters"]]), device["parameters"]))


def source_device(devices_root, dump_dev):
    """A fresh copy of the device's element, from the track Populate named after it."""
    try:
        track = als.find_track(devices_root, dump_dev["class_display_name"])
        for d in als.devices_holder(track):
            if d.tag == dump_dev["class_name"]:
                return d
    except KeyError:
        pass
    return als.find_device(devices_root, dump_dev["class_name"])


def start_set(a):
    root = als.read_set(a.template)
    template = als.find_track(root, a.track) if a.track else als.clip_track(root)
    point_template(template, probe_path(a.probe), a.output, set_tempo(root))
    if not a.keep_returns:
        als.remove_returns(root)
    als.clear_tracks(root)
    return root, template


def point_template(template, probe, output, tempo):
    """Points the template track's clip at `probe` and fits the clip to its length."""
    rate, audio = read_wav(probe)
    als.point_clip_at(template, probe, os.path.dirname(os.path.abspath(output)),
                      frames=len(audio), rate=rate, tempo=tempo)


def set_tempo(root):
    return float(root.find("LiveSet/MainTrack/DeviceChain/Mixer/Tempo/Manual").get("Value"))


def write_out(root, ids, path):
    ids.close()
    als.write_set(root, path)
    # Live 12.4.6 loads no sample of a set outside a Project folder ("Sample Offline", and
    # 'The file "probe.wav" could not be opened' in Log.txt), whatever the clip's Path says;
    # this empty folder is what makes the set's folder a Project
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(path)), PROJECT_INFO), exist_ok=True)


# ---------------------------------------------------------------- calibrate

def changed_value(param):
    """A stored value clearly different from the element's default and inside its range."""
    text = als.manual(param)
    kind = als.stored_kind(text)
    if kind == "bool":
        return "false" if text == "true" else "true"
    v = float(text)
    rng = als.controller_range(param)
    if rng is None:
        return als.format_stored(v + 1 if kind == "int" else (v * 1.5 if v else 0.5), kind)
    lo, hi = rng
    integral = all(float(x).is_integer() for x in (lo, hi, v))
    if integral and hi - lo <= 64:
        return als.format_stored(v + 1 if v + 1 <= hi else v - 1, kind)
    if hi > 1e30:
        return als.format_stored(v * 2 if v > 0 else lo + 1, "float")
    if lo > 0 and hi / lo >= 20:
        picks = [lo * (hi / lo) ** f for f in (0.3, 0.7)]
        far = max(picks, key=lambda p: abs(math.log(p / v)) if v > 0 else p)
    else:
        picks = [lo + (hi - lo) * f for f in (0.3, 0.7)]
        far = max(picks, key=lambda p: abs(p - v))
    return als.format_stored(far, "float")


def cmd_calibrate(a):
    dump = load_json(a.dump)
    devices_root = als.read_set(a.devices)
    root, template = start_set(a)
    ids = als.Ids(root)
    record = {"set": os.path.basename(a.output), "tracks": []}
    for name in a.device:
        dd = dump_device(dump, name)
        dev = source_device(devices_root, dd)
        cls = dd["class_name"]
        als.add_track(root, template, f"ref {cls}", [dev], ids)
        record["tracks"].append({"name": f"ref {cls}", "device": cls, "element": None})
        for path, param in als.parameters(dev):
            d = copy.deepcopy(dev)
            p = als.parameter(d, path)
            new = changed_value(p)
            als.set_manual(p, new)
            tname = f"cal {cls} {path}"
            als.add_track(root, template, tname, [d], ids)
            record["tracks"].append({"name": tname, "device": cls, "element": path,
                                     "default": als.manual(param), "stored": new})
    write_out(root, ids, a.output)
    side = os.path.splitext(a.output)[0] + ".calibration.json"
    with open(side, "w") as f:
        json.dump(record, f, indent=1)
    print(f"wrote {a.output} ({len(record['tracks'])} tracks) and {side}")


# ---------------------------------------------------------------- map

def linear(ends, v):
    """The stored value at API value v when the API range (amin, amax) maps linearly onto the
    controller range (lo, hi); `ends` is (amin, amax, lo, hi)."""
    amin, amax, lo, hi = ends
    return lo + (v - amin) / (amax - amin) * (hi - lo)


def consistent(conv, pairs, ends=None):
    """Whether a conversion fits every (api value, display text, stored value) pair; `ends` is
    (API min, API max, controller min, controller max), for "linear"."""
    used = 0
    for v, disp, s in pairs:
        if conv == "same":
            if abs(v - s) > 1e-5 * max(1.0, abs(s)):
                return False
            used += 1
            continue
        if conv == "integer":
            if not float(v).is_integer() or v != math.trunc(s):
                return False
            used += 1
            continue
        if conv == "linear":
            if ends is None or ends[0] == ends[1] or abs(linear(ends, v) - s) > 1e-4 * max(1.0, abs(s)):
                return False
            used += 1
            continue
        d = disp if isinstance(disp, tuple) else parse_display(disp)
        if d is None:
            return False
        n, unit, half = d
        if math.isinf(n):
            continue
        if UNITS.get(conv, unit) != unit:
            return False
        f = CONVERSIONS[conv]
        try:
            lo, hi = sorted((f(n - half), f(n + half)))
        except OverflowError:
            return False
        slack = 1e-6 * abs(s) + 1e-9
        if not lo - slack <= s <= hi + slack:
            return False
        used += 1
    return used > 0


def log_taper(dp):
    """Whether the display (in base units) follows the API value more closely in log than
    linearly: decides how to interpolate between the dump's samples. Never for dB."""
    pts = []
    for v, text in dp.get("samples", []):
        d = parse_display(text)
        if d is None or not math.isfinite(d[0]):
            continue
        if d[1] == "dB":
            return False
        pts.append((v, d[0]))
    if len(pts) < 3 or any(n <= 0 for _, n in pts):
        return False

    def r2(xs, ys):
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        return 1.0 if sxx == 0 or syy == 0 else sxy * sxy / (sxx * syy)

    vs = [v for v, _ in pts]
    return r2(vs, [math.log(n) for _, n in pts]) > r2(vs, [n for _, n in pts])


def display_is_value(dp):
    """Whether the display's number is the API value itself (Output in dB, Knee)."""
    seen = 0
    for v, text in dp.get("samples", []):
        d = parse_display(text)
        if d is None or not math.isfinite(d[0]):
            continue
        if abs(d[0] - v) > d[2] + 1e-9:
            return False
        seen += 1
    return seen >= 2


def display_at(dp, v):
    """What the control shows at API value v, from the dump, as parse_display gives it: exact at
    the loaded value and at the samples, interpolated between them with a wider margin (the
    Remote Script does not report display text in Live 12.4.6)."""
    if dp is None:
        return None
    if abs(dp["value"] - v) < 1e-7:
        return parse_display(dp["display"])
    pts = [(sv, parse_display(t)) for sv, t in dp.get("samples", [])]
    pts = [(sv, d) for sv, d in pts if d is not None]
    for sv, d in pts:
        if abs(sv - v) < 1e-7:
            return d
    for (v0, d0), (v1, d1) in zip(pts, pts[1:]):
        if v0 <= v <= v1 and math.isfinite(d0[0]) and math.isfinite(d1[0]):
            t = (v - v0) / (v1 - v0)
            if d0[0] > 0 and d1[0] > 0 and log_taper(dp):
                n = math.exp(math.log(d0[0]) + t * math.log(d1[0] / d0[0]))
            else:
                n = d0[0] + t * (d1[0] - d0[0])
            return n, d0[1], max(d0[2], d1[2], 0.25 * abs(d1[0] - d0[0]), 0.01 * abs(n))
    return None


def choose_conversion(qparam, kind, pairs, endpoints, ends=None, samples=()):
    """The conversion for one parameter, or None when nothing fits. `endpoints` are pairs at
    the ends of the range, which break ties; `ends` is (API min, API max, controller min,
    controller max); `samples` the dump's [(API value, display text)]. A display conversion
    whose display is a straight line onto the controller range at every sample becomes
    "linear", which is exact where the display is rounded (Saturator Drive, Amp Bass)."""
    if qparam:
        if kind == "bool":
            ok = all((s != 0) == (v != 0) for v, _, s in pairs)
            return {"convert": "bool"} if ok else None
        offsets = {round(s - v, 6) for v, _, s in pairs}
        return {"convert": "offset", "offset": offsets.pop()} if len(offsets) == 1 else None
    fits = [c for c in PREFERENCE if consistent(c, pairs, ends)]
    if not fits:
        return None
    best = ([c for c in fits if consistent(c, pairs + endpoints, ends)] or fits)[0]
    if best == "same":
        # two calibration points cannot tell an element holding the API value from one holding the
        # displayed number (Redux Jitter: 0.5 at 25 %, API 0.707): when the display is not the API
        # value, a display conversion that fits is the one
        shown = [(v, parse_display(t)) for v, t in samples]
        shown = [(v, d[0]) for v, d in shown if d and math.isfinite(d[0])]
        span = max((v for v, _ in shown), default=0) - min((v for v, _ in shown), default=0)
        for c in ("base", "percent", "ms"):
            f = CONVERSIONS[c]
            if c in fits and span and max(abs(f(n) - v) for v, n in shown) > 0.05 * span:
                best = c
                break
    if best in CONVERSIONS and "linear" in fits:
        line = [(v, d, linear(ends, v)) for v, d in ((v, parse_display(t)) for v, t in samples) if d]
        if line and consistent(best, line):
            best = "linear"
    out = {"convert": best}
    if best == "linear":
        out["range"] = list(ends)
    return out


def cmd_map(a):
    cal = load_json(a.calibration)
    read = load_json(a.read)
    dump = load_json(a.dump)
    devices_root = als.read_set(a.devices)
    live = {t["name"]: t for t in read["tracks"]}
    out = load_json(a.map) if os.path.exists(a.map) else {"live_version": read.get("live_version"), "devices": {}}
    by_dev = {}
    for t in cal["tracks"]:
        by_dev.setdefault(t["device"], []).append(t)
    for cls, rows in by_dev.items():
        dd = dump_device(dump, cls)
        dev = source_device(devices_root, dd)
        dparams = dump_params(dd)
        ref = live.get(f"ref {cls}")
        if ref is None or not ref["devices"]:
            print(f"{cls}: no ref track in {a.read}", file=sys.stderr)
            continue

        def values(track):
            ps = track["devices"][0]["parameters"]
            return dict(zip(keyed([p["name"] for p in ps]), ps))

        refv = values(ref)
        entry = {"display_name": dd["class_display_name"], "params": {}, "unmatched_elements": {}}
        for row in rows:
            if row["element"] is None:
                continue
            t = live.get(row["name"])
            if t is None or not t["devices"]:
                entry["unmatched_elements"][row["element"]] = "track or device missing in Live"
                continue
            now = values(t)
            moved = [k for k in refv if k in now and abs(now[k]["value"] - refv[k]["value"]) > 1e-9]
            if len(moved) != 1:
                entry["unmatched_elements"][row["element"]] = (
                    "no API parameter moved" if not moved else "several moved: " + ", ".join(moved))
                continue
            key = moved[0]
            param = als.parameter(dev, row["element"])
            dp = dparams.get(key)
            pairs = [(x[key]["value"], x[key].get("value_string") or display_at(dp, x[key]["value"]),
                      als.parse_stored(stored))
                     for x, stored in ((refv, row["default"]), (now, row["stored"]))]
            endpoints = []
            ends = None
            rng = als.controller_range(param)
            if rng and dp and dp.get("samples"):
                endpoints = [(dp["samples"][0][0], dp["samples"][0][1], rng[0]),
                             (dp["samples"][-1][0], dp["samples"][-1][1], rng[1])]
            if rng:
                ends = (refv[key]["min"], refv[key]["max"], rng[0], rng[1])
            quantized = bool(refv[key].get("is_quantized"))
            # "1" can be a float element's value: only a quantized parameter's element holds an index
            kind = "bool" if row["default"] in ("true", "false") else ("int" if quantized else "float")
            conv = choose_conversion(quantized, kind, pairs, endpoints, ends, (dp or {}).get("samples", []))
            item = {"element": row["element"], "kind": kind, "points": [[v, s] for v, _, s in pairs]}
            if conv is None:
                item["convert"] = None
                print(f"{cls} {key} ({row['element']}): no conversion fits {pairs}", file=sys.stderr)
            else:
                item.update(conv)
            if key in entry["params"]:
                print(f"{cls} {key}: matched both {entry['params'][key]['element']} and {row['element']}",
                      file=sys.stderr)
            entry["params"][key] = item
        entry["unmatched_params"] = [k for k in refv if k not in entry["params"]]
        out["devices"][cls] = entry
        print(f"{cls}: {len(entry['params'])} parameters mapped, "
              f"{len(entry['unmatched_params'])} without an element, "
              f"{len(entry['unmatched_elements'])} elements without a parameter")
    with open(a.map, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {a.map}")


# ---------------------------------------------------------------- build

def api_value(dp, spec):
    """The API value a value spec means, or raises ValueError."""
    lo, hi = dp["min"], dp["max"]
    if isinstance(spec, (int, float)):
        v = float(spec)
    elif "value" in spec:
        v = float(spec["value"])
    elif "norm" in spec:
        v = lo + (hi - lo) * float(spec["norm"])
    elif "item" in spec:
        items = dp.get("value_items") or []
        if spec["item"] not in items:
            raise ValueError(f"no item {spec['item']!r} (has {', '.join(items)})")
        v = lo + items.index(spec["item"])
    elif "display" in spec:
        v = value_for_display(dp, float(spec["display"]))
    else:
        raise ValueError(f"bad value spec {spec!r}")
    if not lo - 1e-9 <= v <= hi + 1e-9:
        raise ValueError(f"value {v} outside {lo} .. {hi}")
    return round(v) if dp.get("is_quantized") else v


def exponential_fit(dp):
    """(v0, n0, v1, n1) of the exponential through the first and last finite samples, when every
    sample lies within its display rounding of it, else None. A display shown to two places
    (Auto Shift's LFO Rate, 0.01 .. 20 Hz) is too coarse to interpolate between at its low end."""
    pts = []
    for sv, text in dp.get("samples", []):
        d = parse_display(text)
        if d is not None and math.isfinite(d[0]) and d[0] > 0 and d[1] != "dB":
            pts.append((sv, d))
    if len(pts) < 3 or pts[-1][0] == pts[0][0]:
        return None
    (v0, d0), (v1, d1) = pts[0], pts[-1]
    for sv, d in pts:
        n = d0[0] * (d1[0] / d0[0]) ** ((sv - v0) / (v1 - v0))
        if abs(n - d[0]) > d[2] + 1e-9:
            return None
    return v0, d0[0], v1, d1[0]


def interpolate_stored(dp, conv, rng, v):
    """The stored value at API value v: the display number interpolated between the dump's
    samples (in log for a logarithmic taper, never for dB), or the display the dump read at the
    loaded value, and converted. A sample showing -inf or inf stands for the end of the element's
    controller range."""
    f = CONVERSIONS[conv]
    if abs(dp.get("value", math.nan) - v) < 1e-7:
        d = parse_display(dp.get("display", ""))
        if d is not None and math.isfinite(d[0]):
            return f(d[0])
    pts = []
    coarse = False
    for sv, text in dp.get("samples", []):
        d = parse_display(text)
        if d is None:
            continue
        n = d[0]
        if math.isinf(n):
            if rng is None:
                continue
            pts.append((sv, None, rng[0] if n < 0 else rng[1]))
        else:
            pts.append((sv, n, f(n)))
            coarse = coarse or (n > 0 and d[2] > 0.01 * n)
    log = log_taper(dp)
    fit = exponential_fit(dp) if log and coarse else None
    for (v0, n0, s0), (v1, n1, s1) in zip(pts, pts[1:]):
        if not v0 <= v <= v1:
            continue
        t = 0.0 if v1 == v0 else (v - v0) / (v1 - v0)
        if n0 is not None and n1 is not None:
            if fit and n0 > 0 and n1 > 0:
                return f(fit[1] * (fit[3] / fit[1]) ** ((v - fit[0]) / (fit[2] - fit[0])))
            if log and n0 > 0 and n1 > 0:
                return f(math.exp(math.log(n0) + t * (math.log(n1) - math.log(n0))))
            return f(n0 + t * (n1 - n0))
        if s0 > 0 and s1 > 0:
            return math.exp(math.log(s0) + t * (math.log(s1) - math.log(s0)))
        return s0 + t * (s1 - s0)
    return None


def curve(dp):
    """[(api value, display number in base units)] from the dump's samples, finite ones only."""
    pts = []
    for v, text in dp.get("samples", []):
        d = parse_display(text)
        if d is not None and math.isfinite(d[0]):
            pts.append((v, d[0]))
    return pts


def value_for_display(dp, n):
    """The API value whose display reads n (base units), from the sampled curve."""
    if display_is_value(dp):
        return n
    pts = curve(dp)
    log = log_taper(dp)
    for (v0, n0), (v1, n1) in zip(pts, pts[1:]):
        if min(n0, n1) <= n <= max(n0, n1):
            if n1 == n0:
                return v0
            if log and min(n0, n1, n) > 0:
                return v0 + math.log(n / n0) / math.log(n1 / n0) * (v1 - v0)
            return v0 + (n - n0) / (n1 - n0) * (v1 - v0)
    raise ValueError(f"display {n} outside the control's range")


def display_on_line(item, dp):
    """The display conversion that puts every dump sample's display on a "linear" element's line,
    or None (Saturator's Color Amt Low shows -100 .. 100 % for -36 .. 36)."""
    line = [(v, d, linear(item["range"], v))
            for v, d in ((v, parse_display(t)) for v, t in dp.get("samples", [])) if d]
    return next((c for c in PREFERENCE if c in CONVERSIONS and line and consistent(c, line)), None)


def linear_display(item, dp, n):
    """(API value, stored value) for display n (base units) on a "linear" element whose display
    lies on its line: the line inverted, exact where the dump's display text is rounded. None when
    the display is not on the line."""
    conv = display_on_line(item, dp)
    if conv is None:
        return None
    amin, amax, lo, hi = item["range"]
    s = CONVERSIONS[conv](n)
    # the element's range is a float32 (Delay Feedback ends at 0.9499999881, not 0.95), so the
    # control's own end display lies a few parts in 10^8 outside it
    slack = 1e-6 * abs(hi - lo)
    if not min(lo, hi) - slack <= s <= max(lo, hi) + slack:
        raise ValueError(f"display {n} outside the control's range")
    v = min(max(amin + (s - lo) / (hi - lo) * (amax - amin), dp["min"]), dp["max"])
    return v, s


def stored_value(item, dp, spec, rng=None):
    """(API value or None, stored text) for a value spec, through the map entry `item`; `rng` is
    the element's controller range, for display ends that read -inf or inf."""
    kind = item["kind"]
    if isinstance(spec, dict) and "stored" in spec:
        return None, als.format_stored(float(spec["stored"]), kind)
    conv = item.get("convert")
    if conv is None:
        raise ValueError("the map has no conversion for this parameter; use {\"stored\": x}")
    if conv == "linear" and isinstance(spec, dict) and "display" in spec:
        exact = linear_display(item, dp, float(spec["display"]))
        if exact is not None:
            return exact[0], als.format_stored(exact[1], kind)
    v = api_value(dp, spec)
    if conv == "bool":
        return v, als.format_stored(v != 0, "bool")
    if conv == "offset":
        return v, als.format_stored(v + item["offset"], kind)
    if conv == "same":
        return v, als.format_stored(v, kind)
    if conv == "integer":
        return round(v), als.format_stored(round(v), kind)
    if conv == "linear":
        return v, als.format_stored(linear(item["range"], v), kind)
    if isinstance(spec, dict) and "display" in spec:
        n = float(spec["display"])
    else:
        x = interpolate_stored(dp, conv, rng, v)
        if x is None:
            raise ValueError(f"no display near value {v}; use display: or stored:")
        return v, als.format_stored(x, kind)
    return v, als.format_stored(CONVERSIONS[conv](n), kind)


# ---------------------------------------------------------------- stored elements and automation

# the time Live gives an envelope's first event, which holds the value before the song starts
BEFORE_SONG = "-63072000"
EVENTS = {"float": "FloatEvent", "int": "EnumEvent", "bool": "BoolEvent"}


def is_element(name):
    return name.startswith("@")


def set_element(dev, name, value):
    """Writes a stored-element override (`@<path>`) into a device; returns the stored text."""
    path = name[1:]
    el = dev.find(path)
    if el is None:
        raise ValueError(f"{dev.tag} has no element {path!r}")
    target = el.find("Manual") if el.find("Manual") is not None else el
    old = target.get("Value")
    if old is None:
        raise ValueError(f"element {path!r} has no stored value")
    if isinstance(value, str):
        text = value
    else:
        kind = als.stored_kind(old)
        if kind == "bool":
            if value not in (0, 1, True, False):
                raise ValueError(f"element {path!r} is on/off, not {value!r}")
            text = als.format_stored(bool(value), "bool")
        else:
            # a parameter element (Manual with a controller range) is continuous even when its
            # stored value happens to be whole (Utility's MidSideBalance, 1 in 0 .. 2)
            rng = als.controller_range(el) if el.find("Manual") is not None else None
            if rng is not None and not min(rng) - 1e-9 <= float(value) <= max(rng) + 1e-9:
                raise ValueError(f"element {path!r}: {value!r} outside {rng[0]:g} .. {rng[1]:g}")
            if kind == "int" and not float(value).is_integer() and rng is None:
                raise ValueError(f"element {path!r} holds whole numbers, not {value!r}")
            whole = kind == "int" and float(value).is_integer()
            text = als.format_stored(value, "int") if whole else als.format_stored(float(value), "float")
    target.set("Value", text)
    return text


def is_auto(spec):
    return isinstance(spec, dict) and "auto" in spec


def auto_points(item, dp, spec, rng=None):
    """[(beat, API value or None, stored text, curve or None)] for an automation spec, in time
    order. A point may carry a third item, [x1, y1, x2, y2], the Bezier control points of the
    segment that starts at it (Live stores them on the point)."""
    pts = spec["auto"]
    if not pts:
        raise ValueError("an automation lane needs at least one point")
    out = []
    for t, s, *bend in pts:
        if is_auto(s):
            raise ValueError("an automation point cannot itself be automated")
        v, text = stored_value(item, dp, s, rng)
        if bend and len(bend[0]) != 4:
            raise ValueError("a point's curve is its two control points [x1, y1, x2, y2]")
        out.append((float(t), v, text, tuple(float(c) for c in bend[0]) if bend else None))
    if any(b[0] < a[0] for a, b in zip(out, out[1:])):
        raise ValueError("automation points must be in time order")
    return out


def write_envelope(track, element, kind, points):
    """Adds an arrangement envelope for the parameter `element` (already in the track) that
    follows `points` [(beat, _, stored text, curve or None)]."""
    target = element.find("AutomationTarget").get("Id")
    holder = track.find("AutomationEnvelopes/Envelopes")
    if holder is None:
        raise ValueError("the template track has no AutomationEnvelopes")
    env = ET.SubElement(holder, "AutomationEnvelope", Id=str(len(holder)))
    ET.SubElement(ET.SubElement(env, "EnvelopeTarget"), "PointeeId", Value=target)
    auto = ET.SubElement(env, "Automation")
    events = ET.SubElement(auto, "Events")
    tag = EVENTS[kind]
    ET.SubElement(events, tag, Id="0", Time=BEFORE_SONG, Value=points[0][2])
    for i, (t, _, text, bend) in enumerate(points, 1):
        ev = ET.SubElement(events, tag, Id=str(i), Time=format(t, ".10g"), Value=text)
        if bend:
            for name, c in zip(("CurveControl1X", "CurveControl1Y", "CurveControl2X", "CurveControl2Y"), bend):
                ev.set(name, format(c, ".10g"))
    view = ET.SubElement(auto, "AutomationTransformViewState")
    ET.SubElement(view, "IsTransformPending", Value="false")
    ET.SubElement(view, "TimeAndValueTransforms")


def probe_path(p):
    """A probe's WAV: a name from probes.py (made if missing) or a path."""
    return probes.path(p) if p in probes.PROBES else os.path.abspath(p)


def case_probe(spec, path, default):
    """The probe a cases file asks for (`"probe"`: a name from probes.py, or a path relative to
    the repository or to the file), or `default`."""
    p = spec.get("probe")
    if not p:
        return probe_path(default)
    if p in probes.PROBES:
        return probes.path(p)
    for base in (ROOT, os.path.dirname(os.path.abspath(path))):
        if os.path.exists(os.path.join(base, p)):
            return os.path.abspath(os.path.join(base, p))
    raise SystemExit(f"{path}: probe {p} not found")


def cmd_build(a):
    dump = load_json(a.dump)
    devices_root = als.read_set(a.devices)
    amap = load_json(a.map)["devices"]
    root, template = start_set(a)
    tempo = set_tempo(root)
    templates = {probe_path(a.probe): template}
    ids = als.Ids(root)
    out = {"set": os.path.basename(a.output), "generated_by": "make_als.py", "cases": [], "keys": {}}
    problems = 0
    shared = {}  # (probe, device, stored values) -> track name, with --share
    keys = {}  # key wav -> its track's Id

    def key_target(path):
        if path in probes.PROBES:
            path = os.path.relpath(probes.path(path), ROOT)
        wav = next((os.path.abspath(os.path.join(b, path)) for b in (ROOT, os.getcwd())
                    if os.path.exists(os.path.join(b, path))), None)
        if wav is None:
            raise ValueError(f"key {path} not found")
        if wav not in keys:
            t = copy.deepcopy(template)
            point_template(t, wav, a.output, tempo)
            name = "key " + os.path.splitext(os.path.basename(wav))[0]
            keys[wav] = als.add_track(root, t, name, [], ids).get("Id")
            out["keys"][name] = {"wav": os.path.relpath(wav, ROOT), "track_id": keys[wav]}
        return f"AudioIn/Track.{keys[wav]}/PostFxOut"

    midi = {}  # a clip's JSON -> its MIDI track's Id
    midi_src = {}

    def midi_target(spec, out_point):
        import midi_set  # imports this module, so only when needed
        clip = midi_set.norm_clip(spec)
        k = json.dumps(clip, sort_keys=True)
        if k not in midi:
            if not midi_src:
                mroot = als.read_set(midi_set.DEFAULTS["template"])
                midi_src["track"] = als.find_track(mroot, midi_set.DEFAULTS["track"])
                midi_src["clip"] = copy.deepcopy(midi_set.clip_skeleton(mroot))
            name = "midi " + (spec.get("name") or str(len(midi) + 1))
            t = als.add_track(root, midi_src["track"], name, [], ids)
            midi_set.arrangement_events(t).append(midi_set.make_clip(midi_src["clip"], clip, 0.0, name))
            midi[k] = t.get("Id")
            out["keys"][name] = {"midi": clip, "track_id": midi[k]}
        return f"MidiIn/Track.{midi[k]}/{out_point}"

    for path in a.cases:
        spec = load_json(path)
        run = os.path.splitext(os.path.basename(path))[0]
        probe = case_probe(spec, path, a.probe)
        if probe not in templates:
            templates[probe] = copy.deepcopy(template)
            point_template(templates[probe], probe, a.output, tempo)
        dd = dump_device(dump, spec["device"])
        cls = dd["class_name"]
        if cls not in amap:
            raise SystemExit(f"{path}: {cls} is not in the map yet; calibrate it first")
        dparams = dump_params(dd)
        mparams = amap[cls]["params"]
        fresh = source_device(devices_root, dd)
        for case in spec["cases"]:
            dev = copy.deepcopy(fresh)
            rec = {"id": f"{run} {case['id']}", "run": run, "case": case["id"], "device": cls,
                   "probe": os.path.relpath(probe, ROOT), "params": {}, "errors": []}
            lanes = []  # (element path, kind, points) of the case's automation
            for name, vspec in (case.get("params") or {}).items():
                if is_element(name):
                    try:
                        if isinstance(vspec, str) and vspec.startswith("key:"):
                            vspec = key_target(vspec[4:])
                        elif isinstance(vspec, dict) and "midi" in vspec:
                            vspec = midi_target(vspec["midi"], vspec.get("out", "TrackOut"))
                        text = set_element(dev, name, vspec)
                    except ValueError as e:
                        rec["errors"].append(f"{name}: {e}")
                        continue
                    rec.setdefault("elements", {})[name[1:]] = text
                    continue
                item, dp = mparams.get(name), dparams.get(name)
                if item is None or dp is None:
                    rec["errors"].append(f"{name}: not in the map" if dp else f"no parameter {name}")
                    continue
                el = als.parameter(dev, item["element"])
                try:
                    if is_auto(vspec):
                        pts = auto_points(item, dp, vspec, als.controller_range(el))
                        v, text = pts[0][1], pts[0][2]
                    else:
                        pts = None
                        v, text = stored_value(item, dp, vspec, als.controller_range(el))
                except ValueError as e:
                    rec["errors"].append(f"{name}: {e}")
                    continue
                als.set_manual(el, text)
                rec["params"][name] = {"value": v, "element": item["element"], "stored": text}
                first = vspec["auto"][0][1] if pts else vspec
                if isinstance(first, dict) and "display" in first and dp.get("samples"):
                    # the API value is only known to within the samples the display was read at
                    rec["params"][name]["tol"] = 1.0 / (len(dp["samples"]) - 1)
                if pts:
                    rec["params"][name]["auto"] = [[t, x, s] + ([list(c)] if c else []) for t, x, s, c in pts]
                    lanes.append((item["element"], item["kind"], pts))
            problems += len(rec["errors"])
            # the device's whole stored state and its lanes, so cases that differ only in how they
            # were written share
            key = (probe, cls, ET.tostring(dev),
                   tuple((e, tuple(p)) for e, _, p in lanes))
            if a.share and key in shared:
                rec["track"] = shared[key]
            else:
                t = als.add_track(root, templates[probe], rec["id"], [dev], ids)
                (placed,) = list(als.devices_holder(t))
                for element, kind, pts in lanes:
                    write_envelope(t, als.parameter(placed, element), kind, pts)
                rec["track"] = shared[key] = rec["id"]
            out["cases"].append(rec)
    write_out(root, ids, a.output)
    side = os.path.splitext(a.output)[0] + ".cases.json"
    with open(side, "w") as f:
        json.dump(out, f, indent=1)
    tracks = len({c["track"] for c in out["cases"]})
    print(f"wrote {a.output} ({tracks} tracks for {len(out['cases'])} cases) and {side}"
          + (f"; {problems} problems (see the errors in {side})" if problems else ""))
    for rec in out["cases"]:
        for e in rec["errors"]:
            print(f"  {rec['id']}: {e}", file=sys.stderr)
    return 1 if problems else 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, template=True):
        p.add_argument("--dump", default=DEFAULTS["dump"])
        p.add_argument("--devices", default=DEFAULTS["devices"],
                       help="a set with a fresh copy of each device (Populate's)")
        if template:
            p.add_argument("--template", default=DEFAULTS["template"],
                           help="a set with an audio track holding the probe clip, Warp off")
            p.add_argument("--track", default=DEFAULTS["track"],
                           help="that track's name (default: the first audio track with a clip)")
            p.add_argument("--keep-returns", action="store_true")
            p.add_argument("--probe", default=DEFAULTS["probe"],
                           help="the probe the clip plays: a name from probes.py or a WAV at the set's sample rate (its length sets the clip's)")
            p.add_argument("-o", "--output", required=True)

    c = sub.add_parser("calibrate")
    common(c)
    c.add_argument("--device", action="append", required=True, help="class or display name, repeatable")
    m = sub.add_parser("map")
    common(m, template=False)
    m.add_argument("calibration")
    m.add_argument("read")
    m.add_argument("--map", default=DEFAULTS["map"])
    b = sub.add_parser("build")
    common(b)
    b.add_argument("cases", nargs="+")
    b.add_argument("--map", default=DEFAULTS["map"])
    b.add_argument("--share", action="store_true",
                   help="one track for cases whose device ends up stored the same (and same probe)")
    a = ap.parse_args(argv)
    return {"calibrate": cmd_calibrate, "map": cmd_map, "build": cmd_build}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
