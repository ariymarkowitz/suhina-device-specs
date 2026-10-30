# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Renders each track of a Live Set through an implementation under test, one track at a time.

    python render_set.py cases.als -o renders/mine --command "mytool render {set} -o {out} --rate {rate}"
        [--only id,id] [--rate 48000] [--jobs 4]

For every track (or those named in --only) writes a copy of the set beside the original with all
other tracks removed (so the implementation does not run their devices), runs --command on it,
and expects <out>/<track name>.wav. A group the track sits in stays, switched on, as does the
chain of tracks inside a group that is rendered; any other track left in is switched off (the
mixer's track on/off, `Speaker`). --jobs runs several renders at once. The copy sits beside the original so the set's relative paths to
its audio still resolve, and is removed afterwards.

--command is the implementation's own offline renderer of a Live Set, with {set} (the copy),
{out} (the WAV to write) and {rate} (the sample rate) filled in. It is split like a shell
command line but run without a shell.
"""

import argparse
import gzip
import os
import re
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

TRACK_TAGS = ("AudioTrack", "MidiTrack", "GroupTrack")


def read_set(path):
    with open(path, "rb") as f:
        raw = f.read()
    gz = raw[:2] == b"\x1f\x8b"
    if gz:
        raw = gzip.decompress(raw)
    root = ET.fromstring(raw)
    if root.tag != "Ableton" or root.find("LiveSet") is None:
        raise ValueError(f"{path}: not a Live Set")
    return root, gz


def tracks(root):
    holder = root.find("LiveSet/Tracks")
    return [] if holder is None else [t for t in holder if t.tag in TRACK_TAGS]


def track_name(track):
    for p in ("Name/EffectiveName", "Name/UserName"):
        e = track.find(p)
        if e is not None and e.get("Value"):
            return e.get("Value")
    return f"track-{track.get('Id', '?')}"


def set_speaker(track, on):
    sp = track.find("DeviceChain/Mixer/Speaker/Manual")
    if sp is None:
        mixer = track.find("DeviceChain/Mixer")
        if mixer is None:
            return False
        speaker = mixer.find("Speaker")
        if speaker is None:
            speaker = ET.SubElement(mixer, "Speaker")
        sp = ET.SubElement(speaker, "Manual")
    sp.set("Value", "true" if on else "false")
    return True


def group_of(track):
    e = track.find("TrackGroupId")
    gid = None if e is None else e.get("Value")
    return None if gid in (None, "", "-1") else gid


def solo_copy(root, keep):
    """The set's XML with only track number `keep` left in, on, and the groups it needs: the
    groups it sits in (on) and the tracks inside it when it is a group (off, as before)."""
    copy = ET.fromstring(ET.tostring(root))
    holder = copy.find("LiveSet/Tracks")
    all_tracks = tracks(copy)
    by_id = {t.get("Id"): t for t in all_tracks}
    wanted = {id(all_tracks[keep])}
    parent = group_of(all_tracks[keep])
    while parent is not None and parent in by_id and id(by_id[parent]) not in wanted:
        wanted.add(id(by_id[parent]))
        parent = group_of(by_id[parent])
    inside = {all_tracks[keep].get("Id")}
    grew = True
    while grew:
        grew = False
        for t in all_tracks:
            if id(t) not in wanted and group_of(t) in inside:
                wanted.add(id(t))
                inside.add(t.get("Id"))
                grew = True
    for i, t in enumerate(all_tracks):
        if id(t) not in wanted:
            holder.remove(t)
        else:
            set_speaker(t, i == keep or inside.isdisjoint({t.get("Id")}))
    return copy


def write_set(root, path, gz):
    data = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root)
    with open(path, "wb") as f:
        f.write(gzip.compress(data) if gz else data)


def safe_name(name):
    s = re.sub(r"[^A-Za-z0-9._+-]+", "_", name).strip("._")
    return s or "track"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("set", help="the Live Set (.als) with the built cases")
    ap.add_argument("-o", "--out", default="renders/mine")
    ap.add_argument("--only", help="comma-separated track names")
    ap.add_argument("--rate", type=int, default=48000)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1,
                    help="renders at once (default: the number of cores)")
    ap.add_argument("--command", required=True,
                    help="the renderer's command line, with {set}, {out} and {rate}")
    a = ap.parse_args(argv)
    try:
        template = shlex.split(a.command)
    except ValueError as e:
        ap.error(f"--command: {e}")
    if not template or not any("{set}" in w for w in template) or not any("{out}" in w for w in template):
        ap.error("--command needs {set} and {out}")
    root, gz = read_set(a.set)
    all_tracks = tracks(root)
    names = [track_name(t) for t in all_tracks]
    wanted = set(a.only.split(",")) if a.only else None
    os.makedirs(a.out, exist_ok=True)
    folder = os.path.dirname(os.path.abspath(a.set))
    def render_one(i, name):
        tmp = os.path.join(folder, f".render-set-{os.getpid()}-{i}.als")
        out = os.path.join(a.out, safe_name(name) + ".wav")
        error = None
        try:
            write_set(solo_copy(root, i), tmp, gz)
            argv_ = [w.replace("{set}", tmp).replace("{out}", out).replace("{rate}", str(a.rate))
                     for w in template]
            try:
                r = subprocess.run(argv_, capture_output=True, text=True)
                error = None if r.returncode == 0 else (r.stderr.strip() or r.stdout.strip())
            except OSError as e:
                error = str(e)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return name, out, error

    todo = [(i, name) for i, name in enumerate(names) if wanted is None or name in wanted]
    failed = 0
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        for name, out, error in pool.map(lambda job: render_one(*job), todo):
            if error is not None:
                failed += 1
                print(f"{name}: the renderer failed: {error}", file=sys.stderr)
            else:
                print(f"{name}: {out}")
    if wanted is not None:
        missing = wanted - set(names)
        if missing:
            print(f"no tracks named {', '.join(sorted(missing))}", file=sys.stderr)
            failed += len(missing)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
