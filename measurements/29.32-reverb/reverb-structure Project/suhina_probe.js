// Copyright (C) 2026 The Suhina contributors
// SPDX-License-Identifier: GPL-3.0-or-later

// Suhina Probe: the script inside the "Suhina Probe" Max for Live audio effect.
//
// Written against the public Live Object Model documentation only (Cycling '74, "Live Object
// Model" and "LiveAPI"). It passes audio through unchanged (the patcher wires plugin~ to
// plugout~) and answers these messages:
//
//   dump <file>       write every device of the set with all its parameters to <file> (JSON):
//                     name, range, value, default, quantized steps, and the display text at
//                     evenly spaced values, which gives each control's taper and unit
//   samples <n>       how many values of a continuous parameter `dump` samples (default 65)
//   build <file>      read a cases file (JSON, made by harness/cases.py) and make one copy of
//                     this track per case, named after the case, with the device right of the
//                     probe set to the case's values; writes <file>.built.json beside it
//   populate          add one audio track per Live 12 audio effect, each holding a fresh copy
//                     of that device (needs Track.insert_device, Live 12.3 or later)
//
// The Max `js` object runs an old JavaScript engine: ES5 only (var, no arrow functions).

autowatch = 1;
inlets = 1;
outlets = 1;

var SAMPLES = 65;
var MAX_STEPS = 512;
var CHUNK = 16000;

// Live 12 audio effects (manual chapter 29), by the names the browser shows.
var AUDIO_EFFECTS = [
    "Amp", "Auto Filter", "Auto Pan-Tremolo", "Auto Shift", "Beat Repeat", "Cabinet",
    "Channel EQ", "Chorus-Ensemble", "Compressor", "Corpus", "Delay", "Drum Buss",
    "Dynamic Tube", "Echo", "EQ Eight", "EQ Three", "Erosion", "External Audio Effect",
    "Filter Delay", "Gate", "Glue Compressor", "Grain Delay", "Hybrid Reverb", "Limiter",
    "Looper", "Multiband Dynamics", "Overdrive", "Pedal", "Phaser-Flanger", "Redux",
    "Resonators", "Reverb", "Roar", "Saturator", "Shifter", "Spectral Resonator",
    "Spectral Time", "Spectrum", "Tuner", "Utility", "Vinyl Distortion", "Vocoder"
];

// ---------------------------------------------------------------- small helpers

function status(text) {
    outlet(0, "set", text);
    post("Suhina Probe: " + text + "\n");
}

// LiveAPI.get returns arrays; a string property can come back split into words.
function one(v) {
    if (Array.isArray(v)) {
        if (v.length === 1) { return v[0]; }
        return v.join(" ");
    }
    return v;
}

function num(v) {
    var n = Number(one(v));
    return isFinite(n) ? n : null;
}

function str(v) {
    var s = one(v);
    return s === undefined || s === null ? "" : String(s);
}

function list(v) {
    if (Array.isArray(v)) { return v; }
    if (v === undefined || v === null) { return []; }
    return [v];
}

function unquote(path) {
    return str(path).replace(/^"|"$/g, "");
}

function api(path) {
    var a = new LiveAPI(path);
    if (!a || str(a.id) === "0") { return null; }
    return a;
}

function liveVersion() {
    var app = api("live_app");
    if (!app) { return ""; }
    return [num(app.call("get_major_version")), num(app.call("get_minor_version")),
            num(app.call("get_bugfix_version"))].join(".");
}

// ---------------------------------------------------------------- display parsing

// "1.20 kHz" -> {n: 1200, unit: "Hz"}, "350 ms" -> {n: 0.35, unit: "s"}, "-inf dB" -> -Infinity.
function parseDisplay(text) {
    var s = String(text).replace(/−/g, "-").trim();
    if (/^-\s*inf/i.test(s)) { return { n: -Infinity, unit: s.replace(/^-\s*inf\s*/i, "") }; }
    if (/^\+?\s*inf/i.test(s)) { return { n: Infinity, unit: s.replace(/^\+?\s*inf\s*/i, "") }; }
    var m = /^([+-]?\d+(?:\.\d+)?)\s*(.*)$/.exec(s);
    if (!m) { return null; }
    var n = Number(m[1]);
    var unit = m[2];
    if (/^khz$/i.test(unit)) { return { n: n * 1000, unit: "Hz" }; }
    if (/^ms$/i.test(unit)) { return { n: n / 1000, unit: "s" }; }
    if (/^s$/i.test(unit)) { return { n: n, unit: "s" }; }
    if (/^hz$/i.test(unit)) { return { n: n, unit: "Hz" }; }
    return { n: n, unit: unit };
}

// ---------------------------------------------------------------- dump

function paramInfo(p) {
    var lo = num(p.get("min"));
    var hi = num(p.get("max"));
    var quantized = num(p.get("is_quantized")) === 1;
    var value = num(p.get("value"));
    var info = {
        name: str(p.get("name")),
        original_name: str(p.get("original_name")),
        min: lo,
        max: hi,
        value: value,
        display: str(p.call("str_for_value", value)),
        is_quantized: quantized
    };
    var def = num(p.get("default_value"));
    if (def !== null) { info.default_value = def; }
    if (quantized) {
        var items = list(p.get("value_items"));
        if (items.length > 0) { info.value_items = items.map(String); }
    }
    info.samples = sampleParam(p, lo, hi, quantized);
    return info;
}

// [value, display text] at evenly spaced values (every step of a quantized parameter).
function sampleParam(p, lo, hi, quantized) {
    var out = [];
    var i, v;
    if (lo === null || hi === null) { return out; }
    if (quantized) {
        var steps = Math.min(Math.round(hi - lo), MAX_STEPS);
        for (i = 0; i <= steps; i++) {
            v = lo + i;
            out.push([v, str(p.call("str_for_value", v))]);
        }
        return out;
    }
    var n = Math.max(SAMPLES, 2);
    for (i = 0; i < n; i++) {
        v = lo + (hi - lo) * i / (n - 1);
        out.push([v, str(p.call("str_for_value", v))]);
    }
    return out;
}

function deviceInfo(path, where) {
    var d = api(path);
    if (!d) { return null; }
    var info = {
        path: path,
        track: where.track,
        name: str(d.get("name")),
        class_name: str(d.get("class_name")),
        class_display_name: str(d.get("class_display_name")),
        type: num(d.get("type")),
        parameters: []
    };
    var count = d.getcount("parameters");
    for (var i = 0; i < count; i++) {
        var p = api(path + " parameters " + i);
        if (!p) { continue; }
        var pi = paramInfo(p);
        pi.index = i;
        info.parameters.push(pi);
    }
    return info;
}

// Every device path in a device list, racks' chains included, in chain order.
function devicePaths(owner, out) {
    var o = api(owner);
    if (!o) { return out; }
    var count = o.getcount("devices");
    for (var i = 0; i < count; i++) {
        var path = owner + " devices " + i;
        out.push(path);
        var d = api(path);
        if (d && num(d.get("can_have_chains")) === 1) {
            var chains = d.getcount("chains");
            for (var c = 0; c < chains; c++) { devicePaths(path + " chains " + c, out); }
        }
    }
    return out;
}

function trackOwners() {
    var set = api("live_set");
    var owners = [];
    if (!set) { return owners; }
    var i;
    var tracks = set.getcount("tracks");
    for (i = 0; i < tracks; i++) { owners.push("live_set tracks " + i); }
    var returns = set.getcount("return_tracks");
    for (i = 0; i < returns; i++) { owners.push("live_set return_tracks " + i); }
    owners.push("live_set master_track");
    return owners;
}

function samples(n) {
    var v = Math.round(Number(n));
    if (v >= 2 && v <= 1025) { SAMPLES = v; status("samples " + v); }
    else { status("samples must be 2 to 1025"); }
}

// Dumps one device per scheduler tick so Live stays responsive in large sets.
function dump(file) {
    var target = joinArgs(arguments);
    if (!target) { status("dump needs a file"); return; }
    var jobs = [];
    var owners = trackOwners();
    for (var t = 0; t < owners.length; t++) {
        var owner = api(owners[t]);
        var trackName = owner ? str(owner.get("name")) : "";
        var paths = devicePaths(owners[t], []);
        for (var j = 0; j < paths.length; j++) { jobs.push({ path: paths[j], track: trackName }); }
    }
    var set = api("live_set");
    var result = {
        suhina_probe: 1,
        live_version: liveVersion(),
        tempo: set ? num(set.get("tempo")) : null,
        samples: SAMPLES,
        devices: []
    };
    var next = 0;
    var step = function () {
        if (next >= jobs.length) {
            if (writeText(target, JSON.stringify(result, null, 1))) {
                status("dumped " + result.devices.length + " devices");
            }
            return;
        }
        var job = jobs[next];
        next += 1;
        var info = deviceInfo(job.path, job);
        if (info) { result.devices.push(info); }
        status("dumping " + next + "/" + jobs.length);
        schedule(step);
    };
    step();
}

// ---------------------------------------------------------------- build cases

function findParam(device, devPath, name) {
    var count = device.getcount("parameters");
    for (var i = 0; i < count; i++) {
        var p = api(devPath + " parameters " + i);
        if (!p) { continue; }
        if (str(p.get("name")) === name || str(p.get("original_name")) === name) { return p; }
    }
    return null;
}

// The internal value for a case's value spec, or a string saying why there is none.
function resolveValue(p, spec) {
    var lo = num(p.get("min"));
    var hi = num(p.get("max"));
    var quantized = num(p.get("is_quantized")) === 1;
    var v;
    if (typeof spec === "number") { v = spec; }
    else if (spec && typeof spec.value === "number") { v = spec.value; }
    else if (spec && typeof spec.norm === "number") { v = lo + (hi - lo) * spec.norm; }
    else if (spec && typeof spec.item === "string") {
        var items = list(p.get("value_items")).map(String);
        var k = items.indexOf(spec.item);
        if (k < 0) { return "no item '" + spec.item + "' (has " + items.join(", ") + ")"; }
        v = lo + k;
    } else if (spec && typeof spec.display === "number") {
        v = byDisplay(p, lo, hi, spec.display);
        if (typeof v === "string") { return v; }
    } else {
        return "value spec must be a number or {value|norm|item|display}";
    }
    if (v < lo || v > hi) { return "value " + v + " outside " + lo + " .. " + hi; }
    return quantized ? Math.round(v) : v;
}

// Finds the value whose display text reads `target` (base units: Hz, s, dB, %). Displays are
// rounded, so a whole interval of values shows the target: this returns its middle. Assumes the
// display is monotonic over the range, as Live's controls are.
function byDisplay(p, lo, hi, target) {
    var bad = false;
    var at = function (v) {
        var d = parseDisplay(str(p.call("str_for_value", v)));
        if (!d) { bad = true; return 0; }
        return d.n;
    };
    var dlo = at(lo);
    var dhi = at(hi);
    if (bad) { return "display is not numeric"; }
    var sign = dhi >= dlo ? 1 : -1;
    var t = sign * target;
    if (t < sign * dlo || t > sign * dhi) {
        return "display " + target + " outside " + Math.min(dlo, dhi) + " .. " + Math.max(dlo, dhi);
    }
    // first value showing at least the target, and last value showing at most the target
    var edge = function (atLeast) {
        var a = lo;
        var b = hi;
        for (var i = 0; i < 60; i++) {
            var mid = (a + b) / 2;
            var d = sign * at(mid);
            if (atLeast ? d >= t : d > t) { b = mid; } else { a = mid; }
        }
        return atLeast ? b : a;
    };
    var first = edge(true);
    var last = edge(false);
    if (bad) { return "display is not numeric inside the range"; }
    return last >= first ? (first + last) / 2 : first;
}

function probePosition() {
    var me = api("this_device");
    if (!me) { return null; }
    var m = /^live_set tracks (\d+) devices (\d+)$/.exec(unquote(me.path));
    if (!m) { return null; }
    return { track: Number(m[1]), device: Number(m[2]) };
}

function build(file) {
    var source = joinArgs(arguments);
    var text = readText(source);
    if (text === null) { return; }
    var spec;
    try { spec = JSON.parse(text); } catch (e) { status("cases file is not JSON: " + e); return; }
    if (!spec || !Array.isArray(spec.cases)) { status("cases file has no \"cases\" list"); return; }
    var here = probePosition();
    if (!here) { status("put the probe on an audio track, left of the device to test"); return; }
    var set = api("live_set");
    var targetPath = "live_set tracks " + here.track + " devices " + (here.device + 1);
    var target = api(targetPath);
    if (!target) { status("no device right of the probe"); return; }
    var targetName = str(target.get("class_display_name")) || str(target.get("name"));
    if (spec.device && spec.device !== targetName && spec.device !== str(target.get("name"))) {
        status("cases are for " + spec.device + " but the device here is " + targetName);
        return;
    }
    var built = { source: source, device: targetName, live_version: liveVersion(), cases: [] };
    var problems = 0;
    // Copies appear right below the template, so going backwards keeps the file's order.
    for (var c = spec.cases.length - 1; c >= 0; c--) {
        var kase = spec.cases[c];
        set.call("duplicate_track", here.track);
        var trackPath = "live_set tracks " + (here.track + 1);
        var track = api(trackPath);
        if (!track) { status("could not copy the track"); return; }
        track.set("name", String(kase.id));
        var devPath = trackPath + " devices " + (here.device + 1);
        var device = api(devPath);
        var record = { id: String(kase.id), params: {}, errors: [] };
        var names = kase.params ? Object.keys(kase.params) : [];
        for (var k = 0; k < names.length; k++) {
            var p = device ? findParam(device, devPath, names[k]) : null;
            if (!p) { record.errors.push("no parameter " + names[k]); continue; }
            var v = resolveValue(p, kase.params[names[k]]);
            if (typeof v === "string") { record.errors.push(names[k] + ": " + v); continue; }
            p.set("value", v);
            var now = num(p.get("value"));
            record.params[names[k]] = { value: now, display: str(p.call("str_for_value", now)) };
        }
        problems += record.errors.length;
        built.cases.unshift(record);
    }
    var out = source.replace(/\.json$/i, "") + ".built.json";
    if (writeText(out, JSON.stringify(built, null, 1))) {
        status("built " + built.cases.length + " cases" + (problems ? ", " + problems + " problems (see .built.json)" : ""));
    }
}

// ---------------------------------------------------------------- populate

function populate() {
    var set = api("live_set");
    if (!set) { status("no live set"); return; }
    var failed = [];
    var next = 0;
    var step = function () {
        if (next >= AUDIO_EFFECTS.length) {
            status("populated; " + (failed.length ? "not inserted: " + failed.join(", ") : "all inserted"));
            return;
        }
        var name = AUDIO_EFFECTS[next];
        next += 1;
        set.call("create_audio_track", -1);
        var index = set.getcount("tracks") - 1;
        var trackPath = "live_set tracks " + index;
        var track = api(trackPath);
        if (track) {
            track.set("name", name);
            var before = track.getcount("devices");
            track.call("insert_device", name, before);
            if (track.getcount("devices") <= before) { failed.push(name); }
        } else {
            failed.push(name);
        }
        status("populating " + next + "/" + AUDIO_EFFECTS.length);
        schedule(step);
    };
    step();
}

// ---------------------------------------------------------------- files and scheduling

// A dialog path with spaces can arrive as several atoms.
function joinArgs(args) {
    var parts = [];
    for (var i = 0; i < args.length; i++) { parts.push(String(args[i])); }
    return parts.join(" ");
}

function writeText(path, text) {
    var f = new File(path, "write", "TEXT");
    if (!f.isopen) { status("cannot write " + path); return false; }
    f.eof = 0;
    for (var i = 0; i < text.length; i += CHUNK) { f.writestring(text.substr(i, CHUNK)); }
    f.eof = f.position;
    f.close();
    return true;
}

// No type list: Max does not count a .json file as type TEXT, so a "TEXT" filter refuses it.
function readText(path) {
    var f = new File(path, "read");
    if (!f.isopen) { status("cannot read " + path); return null; }
    var text = "";
    while (f.position < f.eof) {
        var part = f.readstring(Math.min(CHUNK, f.eof - f.position));
        if (!part) { break; }
        text += part;
    }
    f.close();
    return text;
}

var pending = [];
var ticker = null;

function schedule(fn) {
    pending.push(fn);
    if (!ticker) {
        ticker = new Task(function () {
            var job = pending.shift();
            if (!pending.length) { ticker.cancel(); ticker = null; }
            if (job) { job(); }
        }, this);
        ticker.interval = 1;
        ticker.repeat();
    }
}
