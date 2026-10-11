#!/usr/bin/env python3
"""Quản lý icon / ảnh cho Figma design agent. Chỉ dùng thư viện chuẩn.

Agent KHÔNG mở được file Illustrator (.ai). Người dùng xuất ra:
  - assets/source/icons/<tên>.svg     (nguồn vector, để dev dùng; agent không nhúng thẳng)
  - assets/icons/<tên>[--<biến thể>]@<N>x.png   (để đưa vào Figma bằng set_image_fill)
  - assets/images/<tên>[@<N>x].png|jpg
  - assets/source/*.ai                (bản gốc, chỉ lưu trữ)

Lệnh:
  scan                       quét thư mục -> cập nhật assets/ASSET_MANIFEST.json (giữ trường người dùng đã điền)
  check                      kiểm tra manifest/tệp (đuôi giả, quá nặng, thiếu license...)
  resolve <icons|images> <tên> [biến thể]   in đường dẫn tuyệt đối để truyền cho set_image_fill
  missing <tên...>           in những tên chưa có trong manifest (để ghi assets/NEEDED.md)
Mã thoát: 0 ok | 1 có lỗi (check) | 2 sai tham số / không tìm thấy
"""
import argparse
import json
import os
import re
import struct
import sys

ROOT = os.environ.get("FIGMA_AGENT_ASSETS", "assets")
MANIFEST = os.path.join(ROOT, "ASSET_MANIFEST.json")
MAX_BYTES = 1_000_000  # khuyến nghị: ảnh đi qua WebSocket dưới dạng base64, giữ nhỏ cho ổn định
NAME = re.compile(
    r"^(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)(?:--(?P<variant>[a-z0-9]+(?:-[a-z0-9]+)*))?"
    r"(?:@(?P<scale>\d+)x)?\.(?P<ext>png|jpe?g)$")
PNG = b"\x89PNG\r\n\x1a\n"
JPG = b"\xff\xd8\xff"


def sniff(path):
    with open(path, "rb") as f:
        head = f.read(32)
    if head.startswith(PNG):
        w, h = struct.unpack(">II", head[16:24])
        return "png", w, h
    if head.startswith(JPG):
        return "jpg", None, None
    return None, None, None


def load():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    return {"capabilities": {"png_fill": None, "svg_fill": None, "checked_at": None},
            "icons": {}, "images": {}}


def save(m):
    os.makedirs(ROOT, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def rel(p):
    return p.replace(os.sep, "/")


def cmd_scan(a):
    m = load()
    problems = []
    seen_icons, seen_images = set(), set()
    for kind in ("icons", "images"):
        d = os.path.join(ROOT, kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            full = os.path.join(d, fn)
            if not os.path.isfile(full) or fn.startswith("."):
                continue
            mt = NAME.match(fn)
            if not mt:
                problems.append(f"{rel(full)}: tên không theo quy ước (chữ thường, a-z0-9-, "
                                f"[--biến-thể][@Nx].png|jpg)")
                continue
            name, variant = mt["name"], mt["variant"] or "default"
            scale = int(mt["scale"] or 1)
            _, w, h = sniff(full)
            if kind == "icons":
                e = m["icons"].setdefault(name, {})
                e.setdefault("variants", {})[variant] = rel(full)
                e["scale"] = scale
                if w:
                    e["px"] = round(w / scale)
                svg = os.path.join(ROOT, "source", "icons", name + ".svg")
                e["source_svg"] = rel(svg) if os.path.exists(svg) else None
                e.setdefault("license", None)
                e.setdefault("origin", None)
                seen_icons.add(name)
            else:
                e = m["images"].setdefault(name, {})
                e["file"] = rel(full)
                e["scale"] = scale
                if w:
                    e["width"], e["height"] = w, h
                e.setdefault("fill_mode", "FILL")
                e.setdefault("license", None)
                seen_images.add(name)
    for n in set(m["icons"]) - seen_icons:
        problems.append(f"icons/{n}: có trong manifest nhưng tệp không còn")
    for n in set(m["images"]) - seen_images:
        problems.append(f"images/{n}: có trong manifest nhưng tệp không còn")
    save(m)
    print(json.dumps({"icons": len(m["icons"]), "images": len(m["images"]),
                      "problems": problems}, ensure_ascii=False, indent=2))


def cmd_check(a):
    m = load()
    errors, warns = [], []

    def chk(path, label):
        if not path or not os.path.exists(path):
            errors.append(f"{label}: không thấy tệp {path}")
            return
        kind, _, _ = sniff(path)
        if kind is None:
            errors.append(f"{label}: {path} không phải PNG/JPG thật (đổi đuôi từ .ai/.svg/.webp?). "
                          f"Xuất lại từ Illustrator: File > Export > Export for Screens > PNG")
        if os.path.getsize(path) > MAX_BYTES:
            warns.append(f"{label}: {path} nặng {os.path.getsize(path)//1024} KB (> {MAX_BYTES//1000} KB) — nên nén/giảm kích thước")

    for n, e in m["icons"].items():
        if not e.get("variants"):
            errors.append(f"icons/{n}: không có biến thể nào")
        for v, p in e.get("variants", {}).items():
            chk(p, f"icons/{n}[{v}]")
        if not e.get("source_svg"):
            warns.append(f"icons/{n}: thiếu assets/source/icons/{n}.svg (dev sẽ không có vector gốc)")
        if not e.get("license"):
            warns.append(f"icons/{n}: chưa ghi license/nguồn")
    for n, e in m["images"].items():
        chk(e.get("file"), f"images/{n}")
        if not e.get("license"):
            warns.append(f"images/{n}: chưa ghi license/nguồn")
    if m["capabilities"].get("png_fill") is None:
        warns.append("capabilities.png_fill chưa kiểm tra — chạy bước 'asset smoke test' ở Pha 3")
    print(json.dumps({"errors": errors, "warnings": warns}, ensure_ascii=False, indent=2))
    sys.exit(1 if errors else 0)


def cmd_resolve(a):
    m = load()
    e = m.get(a.kind, {}).get(a.name)
    if not e:
        print(json.dumps({"error": f"không có {a.kind}/{a.name} trong manifest"}, ensure_ascii=False))
        sys.exit(2)
    if a.kind == "icons":
        variants = e.get("variants", {})
        v = a.variant or ("default" if "default" in variants else None)
        if v not in variants:
            why = f"không có biến thể '{a.variant}'" if a.variant else "có nhiều biến thể, cần chỉ định một"
            print(json.dumps({"error": f"icons/{a.name} {why}",
                              "available": sorted(variants)}, ensure_ascii=False))
            sys.exit(2)
        path = variants[v]
    else:
        path = e["file"]
    print(os.path.abspath(path))


def cmd_missing(a):
    m = load()
    have = set(m["icons"]) | set(m["images"])
    miss = [n for n in a.names if n not in have]
    print(json.dumps({"missing": miss}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan").set_defaults(fn=cmd_scan)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    s = sub.add_parser("resolve")
    s.add_argument("kind", choices=["icons", "images"])
    s.add_argument("name")
    s.add_argument("variant", nargs="?")
    s.set_defaults(fn=cmd_resolve)
    s = sub.add_parser("missing")
    s.add_argument("names", nargs="+")
    s.set_defaults(fn=cmd_missing)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
