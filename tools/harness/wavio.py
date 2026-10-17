# Copyright (C) 2026 The Suhina contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reads and writes WAV files without anything beyond numpy: PCM 16/24/32-bit and float
32/64-bit, plain or WAVE_FORMAT_EXTENSIBLE. Audio comes back as float64 frames x channels."""

import struct

import numpy as np

PCM = 1
FLOAT = 3
EXTENSIBLE = 0xFFFE


def read_wav(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 12 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError(f"{path}: not a RIFF/WAVE file")
    pos = 12
    fmt = None
    frames = None
    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            tag, channels, rate, _, _, bits = struct.unpack("<HHIIHH", body[:16])
            if tag == EXTENSIBLE and len(body) >= 26:
                tag = struct.unpack("<H", body[24:26])[0]
            fmt = (tag, channels, rate, bits)
        elif cid == b"data":
            frames = body
        pos += 8 + size + (size & 1)
    if fmt is None or frames is None:
        raise ValueError(f"{path}: missing fmt or data chunk")
    tag, channels, rate, bits = fmt
    if channels < 1:
        raise ValueError(f"{path}: no channels")
    if tag == FLOAT and bits == 32:
        x = np.frombuffer(frames, dtype="<f4").astype(np.float64)
    elif tag == FLOAT and bits == 64:
        x = np.frombuffer(frames, dtype="<f8").astype(np.float64)
    elif tag == PCM and bits == 16:
        x = np.frombuffer(frames, dtype="<i2") / 32768.0
    elif tag == PCM and bits == 32:
        x = np.frombuffer(frames, dtype="<i4") / 2147483648.0
    elif tag == PCM and bits == 24:
        n = len(frames) // 3
        b = np.frombuffer(frames[:n * 3], dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        v = np.where(v >= 1 << 23, v - (1 << 24), v)
        x = v / 8388608.0
    else:
        raise ValueError(f"{path}: unsupported format tag {tag} with {bits} bits")
    usable = len(x) - len(x) % channels
    return rate, x[:usable].reshape(-1, channels)


def write_wav(path, rate, audio):
    """Writes float32 WAV; `audio` is frames x channels (or one dimension for mono)."""
    a = np.asarray(audio, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    channels = a.shape[1]
    payload = a.astype("<f4").tobytes()
    fmt = struct.pack("<HHIIHH", FLOAT, channels, int(rate), int(rate) * channels * 4, channels * 4, 32)
    fact = struct.pack("<I", a.shape[0])
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 4 + 8 + len(fmt) + 8 + len(fact) + 8 + len(payload)) + b"WAVE")
        f.write(b"fmt " + struct.pack("<I", len(fmt)) + fmt)
        f.write(b"fact" + struct.pack("<I", len(fact)) + fact)
        f.write(b"data" + struct.pack("<I", len(payload)) + payload)
