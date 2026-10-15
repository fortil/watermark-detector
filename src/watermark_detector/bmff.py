"""Minimal ISO-BMFF (MP4/MOV) reader for metadata key/value items."""
from __future__ import annotations

import struct
from collections.abc import Iterator

MAX_BOXES_PER_LEVEL = 4096
MAX_KEYS = 1024
MAX_VALUE_BYTES = 1 << 20


def iter_boxes(data: bytes, start: int, end: int) -> Iterator[tuple[bytes, int, int]]:
    """Yield (type, payload_start, box_end) for the boxes in data[start:end]."""
    end = min(end, len(data))
    pos = start
    count = 0
    while pos + 8 <= end and count < MAX_BOXES_PER_LEVEL:
        size, btype = struct.unpack(">I4s", data[pos:pos + 8])
        header = 8
        if size == 1:
            if pos + 16 > end:
                return
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header or pos + size > end:
            return
        yield btype, pos + header, pos + size
        count += 1
        pos += size


def find_child(data: bytes, start: int, end: int, box_type: bytes) -> tuple[int, int] | None:
    for t, ps, be in iter_boxes(data, start, end):
        if t == box_type:
            return ps, be
    return None


def _meta_items(data: bytes, ps: int, be: int) -> list[tuple[str, str]]:
    # meta is a FullBox in ISO files and a plain box in QuickTime files. Both layouts
    # put hdlr first, so that is how they are told apart. A meta box that does not
    # start with hdlr is skipped on purpose: the layout is unknown and guessing
    # could read unrelated bytes as keys.
    if data[ps + 8:ps + 12] == b"hdlr":
        ps += 4
    elif data[ps + 4:ps + 8] == b"hdlr":
        pass
    else:
        return []
    keys_box = find_child(data, ps, be, b"keys")
    ilst_box = find_child(data, ps, be, b"ilst")
    if keys_box is None or ilst_box is None:
        return []
    kps, kbe = keys_box
    if kps + 8 > kbe:
        return []
    count = min(struct.unpack(">I", data[kps + 4:kps + 8])[0], MAX_KEYS)
    keys: list[str] = []
    pos = kps + 8
    for _ in range(count):
        if pos + 8 > kbe:
            break
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        if size < 8 or pos + size > kbe:
            break
        keys.append(data[pos + 8:pos + size].decode("utf-8", errors="replace"))
        pos += size
    items: list[tuple[str, str]] = []
    ips, ibe = ilst_box
    for t, cps, cbe in iter_boxes(data, ips, ibe):
        idx = struct.unpack(">I", t)[0]
        if idx < 1 or idx > len(keys):
            continue
        for dt, dps, dbe in iter_boxes(data, cps, cbe):
            if dt != b"data" or dbe - dps < 8:
                continue
            vtype = struct.unpack(">I", data[dps:dps + 4])[0]
            value = data[dps + 8:dbe]
            if vtype != 1 or len(value) > MAX_VALUE_BYTES:
                continue
            items.append((keys[idx - 1], value.decode("utf-8", errors="replace")))
            break
    return items


def mp4_metadata_items(data: bytes) -> list[tuple[str, str, str]]:
    """Return (path, key, value) from moov/udta/meta, then moov/meta."""
    out: list[tuple[str, str, str]] = []
    try:
        moov = find_child(data, 0, len(data), b"moov")
        if moov is None:
            return out
        udta = find_child(data, moov[0], moov[1], b"udta")
        if udta is not None:
            meta = find_child(data, udta[0], udta[1], b"meta")
            if meta is not None:
                out += [("moov/udta/meta", k, v) for k, v in _meta_items(data, *meta)]
        meta = find_child(data, moov[0], moov[1], b"meta")
        if meta is not None:
            out += [("moov/meta", k, v) for k, v in _meta_items(data, *meta)]
    except (struct.error, ValueError, IndexError):
        return out
    return out
