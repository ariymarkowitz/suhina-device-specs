# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reads, edits and writes Live Sets (.als: gzipped XML) for make_als.py.

Everything here comes from sets saved by Live 12.4.6 (README › Clean-room rules): how a set
holds its tracks, devices and parameters, and which ids must be unique. What it relies on:

- A device's parameters are child elements that hold a `Manual` value (the stored value, in the
  element's own units) and an `AutomationTarget`. They can sit deeper than the device's own
  children (`SideChain/OnOff`, `Bands.0/ParameterA/Freq`), so a parameter is named by its path
  below the device element.
- Automation and modulation targets, pointees and the main track's controller targets share one
  id space with `LiveSet/NextPointeeId` above all of them. A copied track or device needs new ids
  there. Ids of other elements (tracks, devices in a chain, clip slots) are local to their list,
  except track ids, which are unique among the set's tracks.
"""

import copy
import gzip
import os
import re
import xml.etree.ElementTree as ET

TRACK_TAGS = ("AudioTrack", "MidiTrack", "GroupTrack", "ReturnTrack")


def read_set(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    root = ET.fromstring(raw)
    if root.tag != "Ableton" or root.find("LiveSet") is None:
        raise ValueError(f"{path}: not a Live Set")
    return root


def write_set(root, path):
    ET.indent(root, space="\t")
    data = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")
    with open(path, "wb") as f:
        f.write(gzip.compress(data))


# ---------------------------------------------------------------- ids

def is_global_id(tag):
    return (tag in ("AutomationTarget", "ModulationTarget", "Pointee")
            or tag.endswith("ModulationTarget")
            or re.fullmatch(r"ControllerTargets\.\d+", tag) is not None)


def global_ids(root):
    return [int(e.get("Id")) for e in root.iter() if "Id" in e.attrib and is_global_id(e.tag)]


class Ids:
    """Hands out fresh ids from the set's NextPointeeId."""

    def __init__(self, root):
        self.next_el = root.find("LiveSet/NextPointeeId")
        used = global_ids(root)
        self.next = max([int(self.next_el.get("Value"))] + [i + 1 for i in used])

    def renumber(self, tree):
        """Gives every global id in `tree` a fresh one and follows references to them inside."""
        new = {}
        for e in tree.iter():
            if "Id" in e.attrib and is_global_id(e.tag):
                new[e.get("Id")] = str(self.next)
                e.set("Id", str(self.next))
                self.next += 1
        for e in tree.iter("PointeeId"):
            if e.get("Value") in new:
                e.set("Value", new[e.get("Value")])
        for e in tree.iter("LomId"):
            e.set("Value", "0")

    def close(self):
        self.next_el.set("Value", str(self.next))


# ---------------------------------------------------------------- tracks

def tracks_holder(root):
    return root.find("LiveSet/Tracks")


def tracks(root, tags=TRACK_TAGS):
    return [t for t in tracks_holder(root) if t.tag in tags]


def track_name(track):
    for p in ("Name/UserName", "Name/EffectiveName"):
        e = track.find(p)
        if e is not None and e.get("Value"):
            return e.get("Value")
    return ""


def set_track_name(track, name):
    for p in ("Name/EffectiveName", "Name/UserName"):
        e = track.find(p)
        if e is not None:
            e.set("Value", name)


def find_track(root, name):
    for t in tracks(root):
        if name in (track_name(t), t.find("Name/EffectiveName").get("Value")):
            return t
    raise KeyError(f"no track named {name!r}")


def clip_track(root):
    for t in tracks(root, ("AudioTrack",)):
        if t.find(".//AudioClip") is not None:
            return t
    raise KeyError("no audio track with a clip")


def devices_holder(track):
    return track.find("DeviceChain/DeviceChain/Devices")


def remove_returns(root):
    """Drops the return tracks and every send to them."""
    holder = tracks_holder(root)
    for t in [t for t in holder if t.tag == "ReturnTrack"]:
        holder.remove(t)
    for sends in root.iter("Sends"):
        for s in [s for s in sends if s.tag == "TrackSendHolder"]:
            sends.remove(s)
    pre = root.find("LiveSet/SendsPre")
    if pre is not None:
        for s in list(pre):
            pre.remove(s)


def clear_tracks(root):
    holder = tracks_holder(root)
    for t in [t for t in holder if t.tag in TRACK_TAGS and t.tag != "ReturnTrack"]:
        holder.remove(t)


def add_track(root, template, name, devices, ids):
    """Appends a copy of `template` named `name` holding copies of `devices` (in order)."""
    t = copy.deepcopy(template)
    set_track_name(t, name)
    env = t.find("AutomationEnvelopes/Envelopes")
    if env is not None:
        for e in list(env):
            env.remove(e)
    holder = devices_holder(t)
    for d in list(holder):
        holder.remove(d)
    for i, d in enumerate(devices):
        d = copy.deepcopy(d)
        d.set("Id", str(i))
        holder.append(d)
    used = [int(x.get("Id")) for x in tracks(root)]
    t.set("Id", str(max(used + [0]) + 1))
    ids.renumber(t)
    # before the return tracks, which Live keeps last
    holder_ = tracks_holder(root)
    first_return = next((i for i, x in enumerate(holder_) if x.tag == "ReturnTrack"), len(holder_))
    holder_.insert(first_return, t)
    return t


# ---------------------------------------------------------------- devices and parameters

def find_device(root, class_name):
    """The first device element of this class in the set (a fresh copy is made by the caller)."""
    for t in tracks(root):
        holder = devices_holder(t)
        if holder is None:
            continue
        for d in holder:
            if d.tag == class_name:
                return d
    raise KeyError(f"no {class_name} device in the set")


def parameters(device):
    """[(path, element)] for every parameter element below `device`, in document order."""
    out = []

    def walk(e, path):
        for c in e:
            p = path + [c.tag]
            if c.find("Manual") is not None and c.find("AutomationTarget") is not None:
                out.append(("/".join(p), c))
            else:
                walk(c, p)

    walk(device, [])
    return out


def parameter(device, path):
    e = device.find(path)
    if e is None or e.find("Manual") is None:
        raise KeyError(f"{device.tag} has no parameter element {path!r}")
    return e


def manual(param):
    return param.find("Manual").get("Value")


def set_manual(param, value):
    param.find("Manual").set("Value", value)


def controller_range(param):
    r = param.find("MidiControllerRange")
    if r is None:
        return None
    return float(r.find("Min").get("Value")), float(r.find("Max").get("Value"))


def format_stored(value, kind):
    """A stored value as Live writes it: true/false, an integer, or a float."""
    if kind == "bool":
        return "true" if value else "false"
    if kind == "int":
        return str(int(round(value)))
    return format(float(value), ".10g")


def parse_stored(text):
    if text in ("true", "false"):
        return 1.0 if text == "true" else 0.0
    return float(text)


def stored_kind(text):
    if text in ("true", "false"):
        return "bool"
    return "int" if re.fullmatch(r"-?\d+", text) else "float"


# ---------------------------------------------------------------- the probe clip

def point_clip_at(track, wav_path, set_dir, frames=None, rate=None, tempo=120.0):
    """Points the track's arrangement clips at `wav_path`; with frames and rate, also fits the
    clip's length to that file (an unwarped clip: loop and scroll times in seconds, end in
    beats)."""
    for ref in track.iter("FileRef"):
        if ref.find("Path") is None:
            continue
        ref.find("Path").set("Value", os.path.abspath(wav_path))
        ref.find("RelativePath").set("Value", os.path.relpath(os.path.abspath(wav_path), set_dir))
        ref.find("OriginalFileSize").set("Value", str(os.path.getsize(wav_path)))
    if frames is None:
        return
    secs = frames / rate
    for clip in track.iter("AudioClip"):
        clip.find("CurrentEnd").set("Value", repr(secs * tempo / 60.0))
        for p in ("Loop/LoopEnd", "Loop/HiddenLoopEnd", "ScrollerTimePreserver/RightTime"):
            clip.find(p).set("Value", repr(secs))
        ref = clip.find("SampleRef")
        ref.find("DefaultDuration").set("Value", str(frames))
        ref.find("DefaultSampleRate").set("Value", str(rate))
