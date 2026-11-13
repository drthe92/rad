#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_static_pages.py — cổng kiểm trang tĩnh SEO/GEO.

Kiểm:
  1. Mỗi folder bài học có `index.html` và `<!-- lesson-sha256 -->` khớp `lesson.md`.
  2. Trang có `<html lang="vi">`, title, meta description, canonical đúng, JSON-LD hợp lệ.
  3. URL bài có trong `sitemap.xml`; sitemap đủ số bài + hub + about.
  4. Tồn tại robots.txt, sitemap.xml, llms.txt, about.html, assets/lesson.css, favicon.
  5. Hub không còn link `view.html?b=`; link nội bộ tuyệt đối trỏ tới file tồn tại.

Dùng:
    python3 tools/check_static_pages.py
    python3 tools/check_static_pages.py --quiet
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://rad.matcauvong.com"
LESSON_RE = re.compile(r"^(\d{3,4})-(.+)$")
SHA_RE = re.compile(r"<!--\s*lesson-sha256:\s*([0-9a-f]{64})\s*-->")
CANON_RE = re.compile(r'<link rel="canonical" href="([^"]+)"')
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
HREF_RE = re.compile(r'href="(/[^"#?]*)"')
IMG_RE = re.compile(r'<img[^>]+src="([^"#?]+)"')
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")

def load_cdn():
    try:
        d = json.loads(open(os.path.join(ROOT, "tools", "r2_manifest.json"), encoding="utf-8").read())
        return (d.get("base") or "").rstrip("/"), set(d.get("files", {}).keys())
    except Exception:
        return "", set()


CDN_BASE, CDN_FILES = load_cdn()

REQUIRED = ["robots.txt", "sitemap.xml", "llms.txt", "about.html",
            "assets/lesson.css", "assets/favicon.svg", "index.html"]


def lessons():
    out = []
    for d in sorted(os.listdir(ROOT)):
        if LESSON_RE.match(d) and os.path.exists(os.path.join(ROOT, d, "lesson.md")):
            out.append(d)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    errors = []

    for f in REQUIRED:
        if not os.path.exists(os.path.join(ROOT, f)):
            errors.append(f"thiếu file gốc: {f}")

    try:
        sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
        locs = set(LOC_RE.findall(sm))
    except FileNotFoundError:
        locs = set()

    dirs = lessons()
    for d in dirs:
        p = os.path.join(ROOT, d, "index.html")
        if not os.path.exists(p):
            errors.append(f"{d}: thiếu index.html")
            continue
        h = open(p, encoding="utf-8").read()
        lp = os.path.join(ROOT, d, "lesson.md")
        sha = hashlib.sha256(open(lp, "rb").read()).hexdigest()
        m = SHA_RE.search(h)
        if not m:
            errors.append(f"{d}: thiếu lesson-sha256")
        elif m.group(1) != sha:
            errors.append(f"{d}: index.html cũ hơn lesson.md (sha lệch)")
        if 'lang="vi"' not in h:
            errors.append(f"{d}: thiếu html lang=vi")
        t = TITLE_RE.search(h)
        if not t or len(t.group(1).strip()) < 10:
            errors.append(f"{d}: title thiếu/ngắn")
        ds = DESC_RE.search(h)
        if not ds or not (50 <= len(ds.group(1)) <= 200):
            errors.append(f"{d}: meta description sai độ dài")
        c = CANON_RE.search(h)
        want = f"{BASE}/{d}/"
        if not c or c.group(1) != want:
            errors.append(f"{d}: canonical sai ({c.group(1) if c else 'thiếu'})")
        lds = LD_RE.findall(h)
        if not lds:
            errors.append(f"{d}: thiếu JSON-LD")
        else:
            try:
                json.loads(lds[0])
            except Exception:
                errors.append(f"{d}: JSON-LD không hợp lệ")
        if want not in locs:
            errors.append(f"{d}: không có trong sitemap")
        # link nội bộ tuyệt đối + ảnh phải tồn tại
        for href in set(HREF_RE.findall(h)):
            t = href.lstrip("/")
            if href.endswith("/"):
                t = os.path.join(t, "index.html")
            if not os.path.exists(os.path.join(ROOT, t)):
                errors.append(f"{d}: link gãy {href}")
        for src in set(IMG_RE.findall(h)):
            if CDN_BASE and src.startswith(CDN_BASE + "/"):
                key = src[len(CDN_BASE) + 1:]
                if key not in CDN_FILES:
                    errors.append(f"{d}: ảnh CDN không có trong manifest: {key}")
                continue
            if src.startswith(("http", "data:")):
                continue
            t = src.lstrip("/") if src.startswith("/") else os.path.join(d, src)
            if not os.path.exists(os.path.join(ROOT, t)):
                errors.append(f"{d}: ảnh gãy {src}")

    try:
        hub = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        if "view.html?b=" in hub:
            errors.append("index.html còn link view.html?b=")
        for href in set(HREF_RE.findall(hub)):
            target = os.path.join(ROOT, href.lstrip("/"))
            if href.endswith("/"):
                target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                errors.append(f"index.html: link gãy {href}")
                if len(errors) > 25:
                    break
    except FileNotFoundError:
        errors.append("thiếu index.html (hub)")

    expect = len(dirs) + 2
    if len(locs) < expect:
        errors.append(f"sitemap chỉ có {len(locs)} URL, cần ≥ {expect}")

    if errors:
        print(f"STATIC FAIL: {len(errors)} lỗi")
        for e in errors[:15]:
            print("  -", e)
        if len(errors) > 15:
            print(f"  … và {len(errors) - 15} lỗi khác")
        return 1

    if not a.quiet:
        print(f"STATIC PASS: {len(dirs)} trang bài + {len(locs)} URL sitemap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
