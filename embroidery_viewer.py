#!/usr/bin/env python3
"""Commander protocol-v1 viewer for machine-embroidery files."""

import html
import base64
import json
import math
import os
import sys

PALETTE = (
    "#e63946", "#457b9d", "#2a9d8f", "#f4a261", "#8338ec",
    "#ff006e", "#3a86ff", "#6a994e", "#bc6c25", "#5e548e",
)
MAX_POINTS = 120_000
COMMAND_MASK = 0x000000FF
STITCH = 0


def fail(message):
    print(json.dumps({"ok": False, "error": str(message)}))
    raise SystemExit(0)


def thread_color(thread, index):
    """Extract a CSS color across pyembroidery releases."""
    for method_name in ("hex_color", "get_hex_color"):
        method = getattr(thread, method_name, None)
        if callable(method):
            value = method()
            if value:
                return str(value)
    value = getattr(thread, "color", None)
    if isinstance(value, int):
        return "#%06x" % (value & 0xFFFFFF)
    if isinstance(value, str) and value:
        return value
    return PALETTE[index % len(PALETTE)]


def stitch_blocks(pattern):
    """Return drawable stitch blocks without jump/trim travel lines."""
    blocks = []
    for index, (stitches, thread) in enumerate(pattern.get_as_stitchblock()):
        points = [(float(s[0]), float(s[1])) for s in stitches]
        if len(points) > 1:
            blocks.append((points, thread_color(thread, index)))
    return blocks


def decimate(blocks, limit=MAX_POINTS):
    total = sum(len(points) for points, _ in blocks)
    stride = max(1, math.ceil(total / limit))
    if stride == 1:
        return blocks, False
    reduced = []
    for points, color in blocks:
        sampled = points[::stride]
        if sampled and sampled[-1] != points[-1]:
            sampled.append(points[-1])
        if len(sampled) > 1:
            reduced.append((sampled, color))
    return reduced, True


def render_svg(pattern, filename):
    blocks = stitch_blocks(pattern)
    if not blocks:
        raise ValueError("design contains no drawable stitches")
    all_points = [point for points, _ in blocks for point in points]
    min_x = min(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_x = max(p[0] for p in all_points)
    max_y = max(p[1] for p in all_points)
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    pad = max(width, height) * 0.04 + 2
    blocks, _ = decimate(blocks)

    paths = []
    for points, color in blocks:
        coords = " ".join("%.2f,%.2f" % (x, y) for x, y in points)
        paths.append(
            '<polyline points="%s" fill="none" stroke="%s" '
            'stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>'
            % (coords, html.escape(color, quote=True))
        )

    stitch_count = sum(
        1 for stitch in pattern.stitches if (int(stitch[2]) & COMMAND_MASK) == STITCH
    )
    color_count = max(len(getattr(pattern, "threadlist", [])), len(blocks))
    size_mm = "%.1f × %.1f mm" % (width / 10.0, height / 10.0)
    view_box = "%.2f %.2f %.2f %.2f" % (
        min_x - pad, min_y - pad, width + 2 * pad, height + 2 * pad
    )
    document = (
        '<div style="background:#f8f5ef;border-radius:8px;padding:16px;text-align:center">'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s" '
        'style="display:block;width:100%%;height:auto;max-height:72vh">%s</svg></div>'
        % (view_box, "".join(paths))
    )
    meta = "%s · %s stitches · %s colors" % (size_mm, format(stitch_count, ","), color_count)
    return {"ok": True, "kind": "html", "html": document, "meta": meta}


def render_thumbnail(pattern, px):
    blocks = stitch_blocks(pattern)
    if not blocks:
        raise ValueError("design contains no drawable stitches")
    blocks, _ = decimate(blocks, limit=35_000)
    all_points = [point for points, _ in blocks for point in points]
    min_x = min(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_x = max(p[0] for p in all_points)
    max_y = max(p[1] for p in all_points)
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    pad = max(width, height) * 0.06 + 2
    paths = []
    for points, color in blocks:
        coords = " ".join("%.2f,%.2f" % (x, y) for x, y in points)
        paths.append(
            '<polyline points="%s" fill="none" stroke="%s" '
            'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
            % (coords, html.escape(color, quote=True))
        )
    size = max(32, min(int(px or 220), 1024))
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="%.2f %.2f %.2f %.2f">'
        '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="8" fill="#f8f5ef"/>%s</svg>'
        % (size, size, min_x - pad, min_y - pad, width + 2 * pad, height + 2 * pad,
           min_x - pad, min_y - pad, width + 2 * pad, height + 2 * pad, "".join(paths))
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return {"ok": True, "mime": "image/svg+xml", "data_base64": encoded}


def render(path, method="viewer.render", px=220):
    if not os.path.isfile(path):
        fail("file not found")
    try:
        from pyembroidery import EmbPattern
    except ImportError:
        fail("pyembroidery is not installed; run: python3 -m pip install -r requirements.txt")
    try:
        pattern = EmbPattern(path)
        result = render_thumbnail(pattern, px) if method == "thumbnail.render" else render_svg(pattern, path)
    except Exception as exc:
        fail("cannot read embroidery design: %s" % exc)
    print(json.dumps(result, ensure_ascii=False))


def convert(params):
    src = params.get("src")
    dst = params.get("dst")
    if not isinstance(src, str) or not src or not isinstance(dst, str) or not dst:
        fail("converter.convert requires src and dst")
    if not os.path.isfile(src):
        fail("source file not found")
    try:
        from pyembroidery import EmbPattern
    except ImportError:
        fail("pyembroidery is not installed; run: python3 -m pip install -r requirements.txt")
    try:
        pattern = EmbPattern(src)
        pattern.write(dst)
    except Exception as exc:
        fail("cannot convert embroidery design: %s" % exc)
    print(json.dumps({"ok": True}))


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) < 3:
        fail("usage: embroidery_viewer.py <method> <paramsJson>")
    if argv[1] not in ("viewer.render", "thumbnail.render", "converter.convert"):
        fail("unknown method: %s" % argv[1])
    try:
        params = json.loads(argv[2])
    except (TypeError, ValueError):
        fail("bad params json")
    if argv[1] == "converter.convert":
        convert(params)
        return
    path = params.get("path")
    if not isinstance(path, str) or not path:
        fail("no path")
    render(path, argv[1], params.get("px", 220))


if __name__ == "__main__":
    main()
