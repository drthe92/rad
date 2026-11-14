#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""optimize_images.py — nén JPEG có kiểm soát giấy phép, giữ nguyên tên file.

Vì sao: ảnh >300 KB chiếm ~25% dung lượng nhưng quyết định tốc độ tải/LCP.
Nén lại JPEG q85 progressive thường còn ~45% mà PSNR trung bình ~41 dB.

Luật cứng:
  - **Không bao giờ** nén ảnh CC BY-ND / CC BY-NC-ND (NoDerivatives) hoặc license
    không rõ — đây là tác phẩm phái sinh trái phép.
  - Giữ nguyên tên + đuôi file → không phải sửa lesson.md / CREDITS.
  - Chỉ ghi khi có `--apply`; mặc định dry-run.
  - Ghi log `tools/optimize_log.jsonl` (sha trước/sau) để không nén lặp (mất chất lượng).

Dùng:
    python3 tools/optimize_images.py --dry-run --min-kb 300
    python3 tools/optimize_images.py --apply --min-kb 300 --backup-dir /tmp/opencode/img-backup
    python3 tools/optimize_images.py --apply --min-kb 100 --quality 85
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "tools" / "optimize_log.jsonl"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
ND_MARKERS = ("BY-NC-ND", "BY-ND", "NO DERIV", "NODERIV")


def license_map():
    """Trả {path: 'nd'|'ok'|'unknown'} từ CREDITS từng bài."""
    out = {}
    for cred in glob.glob(str(ROOT / "*/images/CREDITS.md")):
        d = os.path.dirname(cred)
        for line in open(cred, encoding="utf-8", errors="ignore"):
            m = re.search(r"`?([^`|\s]+\.(?:jpg|jpeg|png|webp|gif))`?", line, re.I)
            if not m:
                continue
            p = os.path.normpath(os.path.join(d, m.group(1)))
            u = line.upper()
            if any(k in u for k in ND_MARKERS):
                out[p] = "nd"
            elif "CC0" in u or "PUBLIC DOMAIN" in u or re.search(r"\bPD\b", u):
                out[p] = "ok"
            elif "CC BY" in u or "BY-NC" in u or "BY-SA" in u:
                out[p] = "ok"
            else:
                out.setdefault(p, "unknown")
    return out


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel_key(path):
    """Khóa log luôn là đường dẫn tương đối để so khớp ổn định."""
    p = os.path.normpath(path)
    return os.path.relpath(p, ROOT) if os.path.isabs(p) else p


def load_log():
    done = {}
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                done[rel_key(r["path"])] = r["sha_after"]
            except Exception:
                pass
    return done


def jpeg_bytes(path, quality):
    im = Image.open(path)
    im = im.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-kb", type=int, default=300)
    ap.add_argument("--quality", type=int, default=85)
    ap.add_argument("--max-kb", type=int, default=0, help="0 = không giới hạn trên")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup-dir", default="/tmp/opencode/img-backup")
    ap.add_argument("--include-png", action="store_true", help="optimize PNG lossless (lợi ích nhỏ)")
    a = ap.parse_args(argv)
    if not a.apply:
        a.dry_run = True

    lic = license_map()
    done = load_log()
    files = [f for f in glob.glob(str(ROOT / "*/images/*"))
             if os.path.splitext(f)[1].lower() in IMG_EXT and not f.endswith("CREDITS.md")]
    sel, skipped_nd, skipped_unknown, already = [], 0, 0, 0
    for f in files:
        p = os.path.normpath(f)
        s = os.path.getsize(p)
        if s < a.min_kb * 1024 or (a.max_kb and s > a.max_kb * 1024):
            continue
        cat = lic.get(p, "unknown")
        if cat == "nd":
            skipped_nd += 1
            continue
        if cat == "unknown":
            skipped_unknown += 1
            continue
        if rel_key(p) in done and done[rel_key(p)] == sha(p):
            already += 1
            continue
        sel.append(p)

    total = sum(os.path.getsize(f) for f in sel)
    print(f"Chọn {len(sel)} ảnh ≥{a.min_kb} KB (nén được) · {total/1048576:.1f} MB")
    print(f"Bỏ qua: {skipped_nd} ảnh ND (không được nén), {skipped_unknown} không rõ license, {already} đã nén trước đó")

    after_total = 0
    rows = []
    for i, f in enumerate(sel, 1):
        try:
            if f.lower().endswith((".jpg", ".jpeg")):
                data = jpeg_bytes(f, a.quality)
            elif a.include_png and f.lower().endswith(".png"):
                im = Image.open(f)
                buf = io.BytesIO()
                im.save(buf, "PNG", optimize=True, compress_level=9)
                data = buf.getvalue()
            else:
                continue
            old = os.path.getsize(f)
            new = len(data)
            if new >= old * 0.98:
                continue
            rows.append((f, old, new))
            after_total += new
            if a.apply:
                sha_before = hashlib.sha256(Path(f).read_bytes()).hexdigest()
                bdir = Path(a.backup_dir) / Path(f).parent.name / "images"
                bdir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, bdir / Path(f).name)
                Path(f).write_bytes(data)
                LOG.parent.mkdir(parents=True, exist_ok=True)
                with open(LOG, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({
                        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "path": rel_key(f), "quality": a.quality,
                        "sha_before": sha_before,
                        "sha_after": hashlib.sha256(data).hexdigest(),
                        "before": old, "after": new,
                    }) + "\n")
        except Exception as e:
            print(f"  ✗ {os.path.relpath(f, ROOT)}: {e}", file=sys.stderr)
        if i % 50 == 0:
            print(f"  … {i}/{len(sel)}")

    saved = total - after_total
    if rows:
        print(f"Kết quả: {len(rows)} ảnh · {total/1048576:.1f} → {after_total/1048576:.1f} MB "
              f"(tiết kiệm {saved/1048576:.1f} MB, {saved/total*100:.0f}%)")
        print("  vd:", ", ".join(f"{Path(f).name} {o//1024}→{n//1024}KB" for f, o, n in rows[:3]))
    if a.dry_run:
        print("DRY-RUN: chưa ghi file nào. Thêm --apply để nén thật (có backup).")
    else:
        print(f"ĐÃ GHI. Backup: {a.backup_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
