import json
import shutil
import struct
import subprocess

import pytest

from fixtures.build import build_mp4_with_keys
from watermark_detector.bmff import mp4_metadata_items

ITEMS = [
    ("major_brand", "isom"),
    ("minor_version", "512"),
    ("compatible_brands", "isomiso2avc1mp41"),
    ("AIGC", "x"),
    ("encoder", "Lavf58.76.100"),
]


def test_zai_like(fx):
    got = mp4_metadata_items(fx["zai_like.mp4"].read_bytes())
    assert [(k, v) for _, k, v in got][:3] == ITEMS[:3]
    assert [k for _, k, _ in got] == [k for k, _ in ITEMS]
    assert {p for p, _, _ in got} == {"moov/udta/meta"}


def test_plain(fx):
    got = mp4_metadata_items(fx["plain.mp4"].read_bytes())
    assert [k for _, k, _ in got] == ["encoder"]


def test_quicktime_layout():
    a = mp4_metadata_items(build_mp4_with_keys(ITEMS, fullbox_meta=True))
    b = mp4_metadata_items(build_mp4_with_keys(ITEMS, fullbox_meta=False))
    assert a == b and len(a) == 5


def _box(t, p):
    return struct.pack(">I", 8 + len(p)) + t + p


def test_hostile():
    ftyp = _box(b"ftyp", b"isom\x00\x00\x02\x00isom")
    assert mp4_metadata_items(ftyp) == []
    big = ftyp + struct.pack(">I4sQ", 1, b"moov", 1 << 40)
    assert mp4_metadata_items(big) == []
    hdlr = _box(b"hdlr", bytes(8) + b"mdta" + bytes(13))
    keys = _box(b"keys", bytes(4) + struct.pack(">I", 10**6))
    meta = _box(b"meta", bytes(4) + hdlr + keys + _box(b"ilst", b""))
    assert mp4_metadata_items(ftyp + _box(b"moov", _box(b"udta", meta))) == []
    # ilst child with index 0 and past the key count
    k = bytes(4) + struct.pack(">I", 1) + struct.pack(">I", 12) + b"mdta" + b"AB"
    data = _box(b"data", struct.pack(">II", 1, 0) + b"v")
    ilst = _box(b"ilst", _box(struct.pack(">I", 0), data) + _box(struct.pack(">I", 5), data))
    meta = _box(b"meta", bytes(4) + hdlr + _box(b"keys", k) + ilst)
    assert mp4_metadata_items(ftyp + _box(b"moov", _box(b"udta", meta))) == []


@pytest.mark.skipif(shutil.which("ffprobe") is None, reason="ffprobe not installed")
def test_ffprobe_crosscheck(fx):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags=AIGC", "-of", "default=nw=1:nk=1", str(fx["zai_like.mp4"])],
        capture_output=True, text=True,
    ).stdout.strip()
    ours = next(v for _, k, v in mp4_metadata_items(fx["zai_like.mp4"].read_bytes()) if k == "AIGC")
    assert json.loads(out) == json.loads(ours)
