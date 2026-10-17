# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Writes the Suhina Probe patcher.

    python3 build_patch.py

writes `Suhina Probe.maxpat` (the device's patcher, for reading and diffing) and
`clipboard.json` (the same boxes and lines in the form Max pastes: `pbcopy < clipboard.json`, then
Edit > Paste in the Max for Live editor). See ../README.md for building the .amxd from them.

The patch: plugin~ wired straight to plugout~ (audio passes unchanged), the js object, and three
clickable message boxes that open a file dialog or send a message to it, plus a status line.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
APPVERSION = {"major": 8, "minor": 6, "revision": 0, "architecture": "x64", "modernui": 1}

boxes = []
lines = []


def box(id_, maxclass, text, rect, inlets, outlets, outlettype=None, present=None, **extra):
    b = {
        "id": id_,
        "maxclass": maxclass,
        "numinlets": inlets,
        "numoutlets": outlets,
        "patching_rect": rect,
    }
    if text is not None:
        b["text"] = text
    if outlets:
        b["outlettype"] = outlettype or [""] * outlets
    if present:
        b["presentation"] = 1
        b["presentation_rect"] = present
    b.update(extra)
    boxes.append({"box": b})


def wire(src, outlet, dst, inlet):
    lines.append({"patchline": {"source": [src, outlet], "destination": [dst, inlet]}})


BUTTON = {"bgcolor": [0.25, 0.25, 0.25, 1.0], "textcolor": [1.0, 1.0, 1.0, 1.0], "fontsize": 11.0}

# audio straight through
box("in", "newobj", "plugin~", [20, 20, 60, 22], 2, 2, ["signal", "signal"])
box("out", "newobj", "plugout~", [20, 380, 60, 22], 2, 0)
wire("in", 0, "out", 0)
wire("in", 1, "out", 1)

box("js", "newobj", "js suhina_probe.js", [200, 300, 120, 22], 1, 1)

# Dump: choose where to write, then "dump <file>"
box("dumpbtn", "message", "Dump parameters", [200, 20, 100, 22], 2, 1, present=[8, 8, 110, 20], **BUTTON)
box("dumpt", "newobj", "t b", [200, 60, 30, 22], 1, 1, ["bang"])
box("dumpdlg", "newobj", "savedialog", [200, 100, 70, 22], 1, 3, ["", "", "bang"])
box("dumppre", "newobj", "prepend dump", [200, 140, 80, 22], 1, 1)
wire("dumpbtn", 0, "dumpt", 0)
wire("dumpt", 0, "dumpdlg", 0)
wire("dumpdlg", 0, "dumppre", 0)
wire("dumppre", 0, "js", 0)

# Build: choose a cases file, then "build <file>"
box("buildbtn", "message", "Build cases", [330, 20, 80, 22], 2, 1, present=[124, 8, 80, 20], **BUTTON)
box("buildt", "newobj", "t b", [330, 60, 30, 22], 1, 1, ["bang"])
box("builddlg", "newobj", "opendialog", [330, 100, 70, 22], 1, 2, ["", "bang"])
box("buildpre", "newobj", "prepend build", [330, 140, 85, 22], 1, 1)
wire("buildbtn", 0, "buildt", 0)
wire("buildt", 0, "builddlg", 0)
wire("builddlg", 0, "buildpre", 0)
wire("buildpre", 0, "js", 0)

# Populate: one track per audio effect
box("popbtn", "message", "Populate", [450, 20, 60, 22], 2, 1, present=[210, 8, 64, 20], **BUTTON)
box("popt", "newobj", "t b", [450, 60, 30, 22], 1, 1, ["bang"])
box("popmsg", "message", "populate", [450, 100, 60, 22], 2, 1)
wire("popbtn", 0, "popt", 0)
wire("popt", 0, "popmsg", 0)
wire("popmsg", 0, "js", 0)

# How finely continuous parameters are sampled (not in the device view)
box("samples", "message", "samples 65", [550, 100, 70, 22], 2, 1)
wire("samples", 0, "js", 0)

# status line
box("status", "message", "Suhina Probe: ready", [200, 340, 260, 22], 2, 1,
    present=[8, 36, 266, 20], bgcolor=[0.12, 0.12, 0.12, 1.0], textcolor=[0.8, 0.8, 0.8, 1.0])
wire("js", 0, "status", 0)

box("title", "comment", "Suhina Probe: dump parameters, build test cases", [20, 420, 300, 20], 1, 0,
    present=[8, 62, 266, 20])

patcher = {
    "patcher": {
        "fileversion": 1,
        "appversion": APPVERSION,
        "classnamespace": "box",
        "rect": [100.0, 100.0, 700.0, 480.0],
        "openinpresentation": 1,
        "devicewidth": 282.0,
        "default_fontsize": 10.0,
        "default_fontname": "Arial",
        "gridsize": [15.0, 15.0],
        "boxes": boxes,
        "lines": lines,
    }
}

clipboard = {"boxes": boxes, "lines": lines, "appversion": APPVERSION, "classnamespace": "box"}

with open(os.path.join(HERE, "Suhina Probe.maxpat"), "w") as f:
    json.dump(patcher, f, indent=1)
with open(os.path.join(HERE, "clipboard.json"), "w") as f:
    json.dump(clipboard, f, indent=1)
print("wrote Suhina Probe.maxpat and clipboard.json")
