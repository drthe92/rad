#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_hub_thumbs.py — sinh biến thể thumbnail 400 px cho bản đồ hub.

Vì sao: hub lazy-load 1.293 ảnh thumbnail nhưng đó là **ảnh gốc** (trung vị ~95 KB,
tổng ~147 MB) trong khi ô ảnh trên hub chỉ cao 140 px → tải thừa. Biến thể
400 px chiều rộng (giữ tỉ lệ) nằm ở prefix R2 riêng `thumbs/` để không lẫn với
6.236 ảnh gốc trong `tools/r2_manifest.json`.

Nguồn: `tools/hub_thumbs.json` (uid → tên file trong `<slug>/images/`) — bảng
thumbnail đã biên tập của hub (do build_index.py dùng). Chỉ sinh biến thể cho ảnh
**đã có trên CDN** (có key trong r2_manifest.json), đúng quy tắc của `thumb_of()`.

Định dạng: đo cả JPEG q80 và WebP q80 trên mẫu (`--compare`); WebP q80 nhỏ hơn
~35 % và không ca nào lớn hơn → chọn WebP q80. Ảnh ≤ 400 px hoặc SVG được giữ
nguyên (SVG vector, không resize).

Kết quả ghi vào `tools/hub_thumbs_variants.json` (commit) + file biến thể thật
trong `.hubthumbs/` (gitignore, để uploader đọc):
    {"prefix": "thumbs", "width": 400, "quality": 80, "format": "webp",
     "items": {"<uid>": {"src": "<slug>/images/<file>", "key": "thumbs/<slug>/<stem>.webp",
                         "sha256": "...", "size": 12345, "w": 400, "h": 260,
                         "orig_size": 160000, "live": false}}}

`live` do `tools/upload_hub_thumbs.py` bật khi object đã nằm trên R2; build_index.py
chỉ trỏ hub sang biến thể khi `live` = true (không bao giờ trỏ vào URL 404).

Dùng:
    python3 tools/make_hub_thumbs.py --compare        # chỉ đo JPEG vs WebP
    python3 tools/make_hub_thumbs.py                  # sinh biến thể + JSON
    python3 tools/make_hub_thumbs.py --limit 20       # thử nhanh
"""
import argparse
import hashlib
import io
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
THUMBS_MAP = TOOLS / "hub_thumbs.json"
MANIFEST = TOOLS / "r2_manifest.json"
OUT_JSON = TOOLS / "hub_thumbs_variants.json"
OUT_DIR = ROOT / ".hubthumbs"

WIDTH = 400
QUALITY = 80
PREFIX = "thumbs"
SKIP_EXT = {".svg", ".gif"}     # vector / ảnh động: giữ ảnh gốc


def load_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def slug_of(uid):
    """Thư mục bài của uid (`001` → `001-tong-quan-he-nguc`)."""
    for p in ROOT.iterdir():
        if p.is_dir() and re.match(r"^\d{3,4}-", p.name) and p.name.split("-", 1)[0] == uid:
            return p.name
    return ""


def collect():
    """[(uid, slug, tên_file, đường_dẫn)] cho ảnh thumbnail đã lên CDN."""
    thumbs = load_json(THUMBS_MAP, {}) or {}
    on_cdn = set((load_json(MANIFEST, {}) or {}).get("files", {}))
    rows = []
    for uid, fn in thumbs.items():
        slug = slug_of(uid)
        if not slug:
            continue
        p = ROOT / slug / "images" / fn
        if not p.exists() or f"{slug}/images/{fn}" not in on_cdn:
            continue
        rows.append((uid, slug, fn, p))
    return rows


def to_rgb(im):
    from PIL import Image
    im = im.convert("RGBA") if (im.mode in ("P", "LA", "PA") or "A" in im.mode) else im.convert("RGB")
    return im


def encode(im, fmt):
    from PIL import Image
    buf = io.BytesIO()
    if fmt == "jpeg":
        if im.mode == "RGBA":
            from PIL import Image as I
            bg = I.new("RGB", im.size, (0, 0, 0))
            bg.paste(im, mask=im.split()[3])
            im = bg
        im.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    else:
        im.save(buf, "WEBP", quality=QUALITY, method=6)
    return buf.getvalue()


def resized(path):
    from PIL import Image, ImageOps
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    im.load()
    im = to_rgb(im)
    w, h = im.size
    if w > WIDTH:
        im = im.resize((WIDTH, max(1, round(h * WIDTH / w))), Image.LANCZOS)
    return im


def cmd_compare(args):
    rows = collect()
    random.seed(7)
    samp = random.sample(rows, min(args.compare, len(rows)))
    tj = tw = tsize = 0
    worse = []
    t0 = time.time()
    for uid, slug, fn, p in samp:
        if p.suffix.lower() in SKIP_EXT:
            continue
        im = resized(p)
        j, w = encode(im, "jpeg"), encode(im, "webp")
        tj += len(j)
        tw += len(w)
        tsize += p.stat().st_size
        if len(w) > len(j):
            worse.append((uid, len(j), len(w)))
    n = len(samp)
    print(f"Mẫu {n} ảnh · gốc {tsize/1024:.0f} KB | JPEG q{QUALITY}: {tj/1024:.0f} KB"
          f" ({(tj/tsize)*100:.0f} % gốc) | WebP q{QUALITY}: {tw/1024:.0f} KB"
          f" ({(tw/tsize)*100:.0f} % gốc, {tw/tj*100:.0f} % JPEG)")
    print(f"WebP lớn hơn JPEG ở {len(worse)}/{n} ảnh · thời gian {time.time()-t0:.1f} s")
    return 0


def main(argv=None):
    global WIDTH, QUALITY
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--compare", type=int, metavar="N",
                    help="chỉ đo JPEG vs WebP trên N ảnh mẫu (không ghi gì)")
    ap.add_argument("--limit", type=int, help="chỉ xử lý N ảnh đầu (thử nhanh)")
    ap.add_argument("--width", type=int, default=400)
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--no-write", action="store_true", help="chỉ in số đo, không ghi")
    args = ap.parse_args(argv)
    WIDTH, QUALITY = args.width, args.quality
    if args.compare:
        return cmd_compare(args)

    rows = collect()
    if args.limit:
        rows = rows[: args.limit]
    old = load_json(OUT_JSON, {}) or {}
    old_items = old.get("items", {}) or {}
    items = {}
    n_new = n_reuse = n_keep = n_fail = 0
    orig_total = var_total = 0
    t0 = time.time()
    for i, (uid, slug, fn, p) in enumerate(rows, 1):
        orig_size = p.stat().st_size
        orig_total += orig_size
        stem = fn.rsplit(".", 1)[0] if "." in fn else fn
        prev = old_items.get(uid) or {}
        key = f"{PREFIX}/{slug}/{stem}.webp"
        if p.suffix.lower() in SKIP_EXT or orig_size <= 0:
            n_keep += 1
            continue
        out = OUT_DIR / slug / f"{stem}.webp"
        # Đã có file + khớp sha của ảnh gốc → tái dùng, không encode lại.
        if (prev.get("key") == key and out.exists() and prev.get("sha256")
                and prev.get("orig_sha256") == sha256_file(p)):
            items[uid] = prev
            var_total += out.stat().st_size
            n_reuse += 1
            continue
        try:
            im = resized(p)
            data = encode(im, "webp")
        except Exception as e:                     # ảnh hỏng: giữ ảnh gốc
            print(f"  ✗ {uid} {fn}: {e}", file=sys.stderr)
            n_fail += 1
            continue
        if len(data) >= orig_size:                 # không lợi → giữ ảnh gốc
            n_keep += 1
            continue
        if not args.no_write:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
        items[uid] = {
            "src": f"{slug}/images/{fn}",
            "key": key,
            "sha256": hashlib.sha256(data).hexdigest(),
            "orig_sha256": sha256_file(p),
            "size": len(data),
            "orig_size": orig_size,
            "w": im.size[0],
            "h": im.size[1],
            "live": bool(prev.get("live") and prev.get("sha256") == hashlib.sha256(data).hexdigest()),
        }
        var_total += len(data)
        n_new += 1
        if i % 100 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)} · {var_total/1048576:.1f} MB biến thể · giữ gốc {n_keep}"
                  f" · tái dùng {n_reuse} · lỗi {n_fail} · {time.time()-t0:.0f} s")

    # Giữ item cũ ngoài phạm vi --limit để không mất bản ghi khi chạy thử.
    for uid, it in old_items.items():
        items.setdefault(uid, it)

    live = sum(1 for it in items.values() if it.get("live"))
    n_var = len(items)
    out_json = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prefix": PREFIX,
        "width": WIDTH,
        "quality": QUALITY,
        "format": "webp",
        "source_map": "tools/hub_thumbs.json",
        "stats": {"n_variants": n_var, "n_live": live, "kept_original": n_keep,
                  "orig_bytes": orig_total, "variant_bytes": var_total},
        "items": dict(sorted(items.items())),
    }
    if not args.no_write:
        OUT_JSON.write_text(json.dumps(out_json, ensure_ascii=False, separators=(",", ":")) + "\n",
                            encoding="utf-8")
    n = n_var
    print(f"XONG: {n} biến thể ({live} đã live) · giữ ảnh gốc {n_keep} · lỗi {n_fail}"
          f" · nguồn {orig_total/1048576:.1f} MB → biến thể {var_total/1048576:.1f} MB"
          f" ({(var_total/orig_total)*100:.1f} %)" if orig_total else "XONG: không có ảnh")
    if n:
        print(f"  trung bình {var_total/n/1024:.1f} KB/biến thể (gốc {orig_total/len(rows)/1024:.1f} KB)")
    print(f"  JSON: {OUT_JSON.relative_to(ROOT)} · file: {OUT_DIR.relative_to(ROOT)}/")
    return 0 if not n_fail else 1


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


if __name__ == "__main__":
    sys.exit(main())
