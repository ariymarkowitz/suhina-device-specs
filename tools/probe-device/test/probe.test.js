// Copyright (C) 2026 The Suhina contributors
// SPDX-License-Identifier: GPL-3.0-or-later

// Runs suhina_probe.js against a mock of the Live Object Model and Max's js globals.
// node --test tools/probe-device/test

"use strict";
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const SCRIPT = fs.readFileSync(path.join(__dirname, "..", "suhina_probe.js"), "utf8");

function param(name, o) {
  return Object.assign({ kind: "param", name, original_name: name, min: 0, max: 1, value: 0,
    is_quantized: 0, value_items: [], display: (v) => v.toFixed(2) }, o);
}

function compressor() {
  return {
    kind: "device", name: "Compressor", class_name: "Compressor2", class_display_name: "Compressor",
    type: 2, can_have_chains: 0, chains: [],
    parameters: [
      param("Device On", { is_quantized: 1, value: 1, value_items: ["off", "on"] }),
      // Threshold: -inf .. 6 dB on a 0..1 control, log-like taper.
      param("Threshold", { value: 1, default_value: 1, display: (v) =>
        v <= 0 ? "-inf dB" : (20 * Math.log10(v) + 6).toFixed(1) + " dB" }),
      // Attack in ms 0.01 .. 1000, display switches to s at 1 s.
      param("Attack", { min: 0.01, max: 1000, value: 2, display: (v) =>
        v >= 1000 ? (v / 1000).toFixed(2) + " s" : v.toFixed(2) + " ms" }),
      param("Model", { is_quantized: 1, max: 2, value_items: ["Peak", "RMS", "Expand"],
        display: (v) => ["Peak", "RMS", "Expand"][Math.round(v)] }),
    ],
  };
}

function probe() {
  return { kind: "device", name: "Suhina Probe", class_name: "MxDeviceAudioEffect",
    class_display_name: "Suhina Probe", type: 2, can_have_chains: 0, chains: [], parameters: [] };
}

function makeLive() {
  const rack = { kind: "device", name: "Audio Effect Rack", class_name: "AudioEffectGroupDevice",
    class_display_name: "Audio Effect Rack", type: 2, can_have_chains: 1, parameters: [],
    chains: [{ kind: "chain", name: "Chain", devices: [compressor()] }] };
  const set = {
    kind: "set", tempo: 120,
    tracks: [
      { kind: "track", name: "Probe", devices: [probe(), compressor()] },
      { kind: "track", name: "Racks", devices: [rack] },
    ],
    return_tracks: [{ kind: "track", name: "A-Reverb", devices: [] }],
    master_track: { kind: "track", name: "Main", devices: [] },
  };
  return { set, thisDevice: "live_set tracks 0 devices 0", insertFails: new Set(["Vocoder"]) };
}

function resolve(live, p) {
  const t = p.trim().split(/\s+/);
  if (t[0] === "this_device") return resolve(live, live.thisDevice + (t.length > 1 ? " " + t.slice(1).join(" ") : ""));
  if (t[0] === "live_app") return { node: { kind: "app" }, path: "live_app" };
  if (t[0] !== "live_set") return null;
  let node = live.set;
  for (let i = 1; i < t.length; i++) {
    const key = t[i];
    if (key === "master_track") { node = node.master_track; continue; }
    const list = node[key];
    const idx = Number(t[++i]);
    if (!Array.isArray(list) || !(idx in list)) return null;
    node = list[idx];
  }
  return { node, path: t.join(" ") };
}

function deepCopyTrack(track) {
  // functions (display) must survive, so copy by hand
  const copyDevice = (d) => Object.assign({}, d, {
    parameters: d.parameters.map((p) => Object.assign({}, p)),
    chains: (d.chains || []).map((c) => Object.assign({}, c, { devices: c.devices.map(copyDevice) })),
  });
  return Object.assign({}, track, { devices: track.devices.map(copyDevice) });
}

function makeGlobals(live, files, log) {
  let nextId = 1;
  function LiveAPI(p) {
    const r = resolve(live, p);
    this.id = r ? String(nextId++) : "0";
    this.path = r ? '"' + r.path + '"' : '""';
    this.node = r && r.node;
  }
  LiveAPI.prototype.get = function (prop) {
    const v = this.node[prop];
    if (v === undefined) return undefined;
    return Array.isArray(v) ? v.slice() : [v];
  };
  LiveAPI.prototype.getcount = function (prop) { return (this.node[prop] || []).length; };
  LiveAPI.prototype.set = function (prop, v) { this.node[prop] = v; };
  LiveAPI.prototype.call = function (fn, ...args) {
    const n = this.node;
    if (fn === "str_for_value") return [n.display(Number(args[0]))];
    if (fn === "get_major_version") return [12];
    if (fn === "get_minor_version") return [4];
    if (fn === "get_bugfix_version") return [6];
    if (fn === "duplicate_track") { n.tracks.splice(args[0] + 1, 0, deepCopyTrack(n.tracks[args[0]])); return; }
    if (fn === "create_audio_track") { n.tracks.push({ kind: "track", name: "Audio", devices: [] }); return; }
    if (fn === "insert_device") {
      if (live.insertFails.has(args[0])) return;
      n.devices.splice(args[1], 0, { kind: "device", name: args[0], class_name: args[0],
        class_display_name: args[0], type: 2, can_have_chains: 0, chains: [], parameters: [] });
      return;
    }
    throw new Error("unmocked call " + fn);
  };

  // Like Max in Live 12.4.6: opening a .json file for reading with the type list "TEXT" fails.
  function File(p, mode, typelist) {
    this.p = p; this.mode = mode;
    this.isopen = mode === "write" || (p in files && !(typelist === "TEXT" && /\.json$/i.test(p)));
    this.data = mode === "write" ? "" : files[p] || ""; this.position = 0;
    this.eof = this.data.length;
  }
  File.prototype.writestring = function (s) {
    assert.ok(s.length <= 32767, "writestring over Max's limit");
    this.data = this.data.slice(0, this.position) + s; this.position += s.length;
  };
  File.prototype.readstring = function (n) {
    assert.ok(n <= 32767, "readstring over Max's limit");
    const s = this.data.substr(this.position, n); this.position += s.length; return s;
  };
  File.prototype.close = function () { if (this.mode === "write") files[this.p] = this.data.slice(0, this.eof); };

  function Task(fn) { this.fn = fn; this.on = false; }
  Task.prototype.repeat = function () {
    this.on = true;
    const tick = () => { if (!this.on) return; this.fn(); if (this.on) setImmediate(tick); };
    setImmediate(tick);
  };
  Task.prototype.cancel = function () { this.on = false; };

  return { LiveAPI, File, Task, post: (s) => log.push(String(s)), outlet: (_, __, s) => log.push("status " + s) };
}

function load(live) {
  const files = {};
  const log = [];
  const ctx = vm.createContext(makeGlobals(live, files, log));
  vm.runInContext(SCRIPT, ctx);
  return { ctx, files, log };
}

function until(log, re) {
  return new Promise((ok, fail) => {
    const start = Date.now();
    const check = () => {
      if (log.some((l) => re.test(l))) return ok();
      if (Date.now() - start > 5000) return fail(new Error("timeout; log: " + log.slice(-5).join(" | ")));
      setImmediate(check);
    };
    check();
  });
}

test("the script is ES5 the Max js object can run", () => {
  const code = SCRIPT.replace(/\/\/.*$/gm, "");
  assert.doesNotMatch(code, /=>|\blet\s|\bconst\s|`|\bclass\s/);
});

test("parseDisplay normalises units", () => {
  const { ctx } = load(makeLive());
  const p = (s) => JSON.parse(JSON.stringify(ctx.parseDisplay(s)));
  assert.deepStrictEqual(p("1.20 kHz"), { n: 1200, unit: "Hz" });
  assert.deepStrictEqual(p("350 ms"), { n: 0.35, unit: "s" });
  assert.deepStrictEqual(p("-12.5 dB"), { n: -12.5, unit: "dB" });
  assert.deepStrictEqual(p("−6 dB"), { n: -6, unit: "dB" });
  assert.strictEqual(ctx.parseDisplay("-inf dB").n, -Infinity);
  assert.strictEqual(ctx.parseDisplay("Peak"), null);
});

test("dump writes every device, racks and all, with samples", async () => {
  const live = makeLive();
  const { ctx, files, log } = load(live);
  ctx.samples(5);
  ctx.dump("Macintosh", "HD:/tmp/dump.json");
  await until(log, /dumped/);
  const out = JSON.parse(files["Macintosh HD:/tmp/dump.json"]);
  assert.strictEqual(out.live_version, "12.4.6");
  assert.strictEqual(out.tempo, 120);
  assert.deepStrictEqual(out.devices.map((d) => d.path), [
    "live_set tracks 0 devices 0", "live_set tracks 0 devices 1",
    "live_set tracks 1 devices 0", "live_set tracks 1 devices 0 chains 0 devices 0"]);
  const comp = out.devices[1];
  assert.strictEqual(comp.class_name, "Compressor2");
  assert.strictEqual(comp.track, "Probe");
  const thr = comp.parameters.find((p) => p.name === "Threshold");
  assert.strictEqual(thr.samples.length, 5);
  assert.strictEqual(thr.samples[0][1], "-inf dB");
  assert.strictEqual(thr.default_value, 1);
  assert.strictEqual(thr.display, "6.0 dB");
  const model = comp.parameters.find((p) => p.name === "Model");
  assert.deepStrictEqual(model.value_items, ["Peak", "RMS", "Expand"]);
  assert.deepStrictEqual(model.samples, [[0, "Peak"], [1, "RMS"], [2, "Expand"]]);
  assert.ok(!("default_value" in model));
});

test("dump writes large output in chunks Max accepts", async () => {
  const live = makeLive();
  const { ctx, files, log } = load(live);
  ctx.samples(1025);
  ctx.dump("/tmp/big.json");
  await until(log, /dumped/);
  assert.ok(files["/tmp/big.json"].length > 32767);
  JSON.parse(files["/tmp/big.json"]);
});

test("build copies the track once per case, in order, and sets values", () => {
  const live = makeLive();
  const { ctx, files } = load(live);
  files["/tmp/cases.json"] = JSON.stringify({ device: "Compressor", cases: [
    { id: "thr-12", params: { Threshold: { display: -12 }, Model: { item: "RMS" } } },
    { id: "atk-1s", params: { Attack: { display: 1 } } },
    { id: "bad", params: { Nope: 1, Model: { item: "Opto" }, Attack: 5000 } },
  ] });
  ctx.build("/tmp/cases.json");
  assert.deepStrictEqual(live.set.tracks.map((t) => t.name), ["Probe", "thr-12", "atk-1s", "bad", "Racks"]);
  const comp = (i) => live.set.tracks[i].devices[1].parameters;
  const thr = comp(1).find((p) => p.name === "Threshold");
  assert.strictEqual(thr.display(thr.value), "-12.0 dB");
  assert.strictEqual(comp(1).find((p) => p.name === "Model").value, 1);
  const atk = comp(2).find((p) => p.name === "Attack");
  assert.strictEqual(ctx.parseDisplay(atk.display(atk.value)).n, 1); // "1000.00 ms" or "1.00 s"
  // the template keeps its values
  assert.strictEqual(comp(0).find((p) => p.name === "Threshold").value, 1);
  const built = JSON.parse(files["/tmp/cases.built.json"]);
  assert.deepStrictEqual(built.cases.map((c) => c.id), ["thr-12", "atk-1s", "bad"]);
  assert.strictEqual(built.cases[0].params.Threshold.display, "-12.0 dB");
  assert.strictEqual(built.cases[2].errors.length, 3);
});

test("build reads a .json cases file from the open dialog's Max-style path", () => {
  const live = makeLive();
  const { ctx, files, log } = load(live);
  files["Macintosh HD:/tmp/my cases.json"] = JSON.stringify({ device: "Compressor", cases: [
    { id: "default", params: {} }] });
  ctx.build("Macintosh", "HD:/tmp/my", "cases.json");
  assert.ok(log.some((l) => /built 1 cases/.test(l)), log.join(" | "));
  assert.ok("Macintosh HD:/tmp/my cases.built.json" in files);
});

test("build refuses cases for another device", () => {
  const live = makeLive();
  const { ctx, files, log } = load(live);
  files["/tmp/c.json"] = JSON.stringify({ device: "Gate", cases: [{ id: "x", params: {} }] });
  ctx.build("/tmp/c.json");
  assert.strictEqual(live.set.tracks.length, 2);
  assert.ok(log.some((l) => /cases are for Gate/.test(l)));
});

test("build says where the probe has to be", () => {
  const live = makeLive();
  live.thisDevice = "live_set master_track devices 0";
  live.set.master_track.devices.push(probe());
  const { ctx, files, log } = load(live);
  files["/tmp/c.json"] = JSON.stringify({ cases: [] });
  ctx.build("/tmp/c.json");
  assert.ok(log.some((l) => /put the probe on an audio track/.test(l)));
});

test("populate adds a track per effect and reports the ones it could not insert", async () => {
  const live = makeLive();
  const { ctx, log } = load(live);
  ctx.populate();
  await until(log, /populated/);
  assert.strictEqual(live.set.tracks.length, 2 + 42);
  assert.strictEqual(live.set.tracks[2].name, "Amp");
  assert.strictEqual(live.set.tracks[2].devices[0].name, "Amp");
  assert.ok(log.some((l) => /not inserted: Vocoder/.test(l)));
});
