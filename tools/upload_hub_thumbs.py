#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""upload_hub_thumbs.py — đưa biến thể thumbnail 400 px lên R2, prefix `thumbs/`.

Vì sao tách khỏi `tools/r2_upload.py`: 6.236 ảnh gốc do `r2_upload.py` quản lý
(`tools/r2_manifest.json`). Biến thể thumbnail phải **không** chen vào manifest đó
(giữ nguyên số khóa để các cổng verify và `cdn.py` không đổi hành vi) → khi upload
xong, bật `"live": true` cho từng item trong `tools/hub_thumbs_variants.json`;
`build_index.py` chỉ trỏ hub sang biến thể có `live` (không bao giờ trỏ URL 404).

Key trên R2: `thumbs/<slug>/<stem>.webp` (song song `<slug>/images/<file>` của gốc).
File nguồn: `.hubthumbs/<slug>/<stem>.webp` do `tools/make_hub_thumbs.py` sinh
(gitignore — chạy generator trước ở máy có ảnh).

Dùng:
    python3 tools/make_hub_thumbs.py               # sinh biến thể (local)
    python3 tools/upload_hub_thumbs.py --plan      # xem cần upload gì
    python3 tools/upload_hub_thumbs.py --upload    # upload (resume theo sha256)
    python3 tools/upload_hub_thumbs.py --verify --sample 15

Exit: 0 OK/SKIP; 1 lỗi; 2 thiếu cấu hình R2 khi cần.
"""
import argparse
import concurrent.futures as cf
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2_upload as r2  # dùng lại SigV4 + s3_request + cfg + have_creds

ROOT = r2.ROOT
VARIANTS = ROOT / "tools" / "hub_thumbs_variants.json"
SRC_DIR = ROOT / ".hubthumbs"


def load_variants():
    try:
        return json.loads(VARIANTS.read_text(encoding="utf-8"))
    except Exception:
        return {"items": {}}


def save_variants(d):
    VARIANTS.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n",
                        encoding="utf-8")


def pending(d):
    """Item chưa live (hoặc sha đổi) + đường dẫn file nguồn tương ứng."""
    out = []
    for uid, it in sorted(d.get("items", {}).items()):
        if it.get("live") and it.get("uploaded_sha256") == it.get("sha256"):
            continue
        key = it.get("key", "")
        rel = key.split("/", 1)[1] if key.startswith("thumbs/") else key
        p = SRC_DIR / rel
        out.append((uid, it, p))
    return out


def upload_one(item, path, attempts=3):
    import hashlib
    import time
    body = path.read_bytes()
    sha = hashlib.sha256(body).hexdigest()
    assert sha == item["sha256"], f"sha lệch {item['key']}"
    last = None
    for i in range(attempts):
        status, hdrs, resp = r2.s3_request(
            "PUT", item["key"], body,
            {"content-type": "image/webp", "cache-control": r2.CACHE_CONTROL,
             "x-amz-meta-sha256": sha})
        if status in (200, 201):
            return {"ok": True, "key": item["key"],
                    "etag": (hdrs.get("ETag") or hdrs.get("etag") or "").strip('"'), "sha256": sha}
        last = f"HTTP {status}: {resp[:200]!r}"
        if status not in (429, 500, 502, 503, 504):
            break
        time.sleep((2 ** i) + random.random())
    return {"ok": False, "key": item["key"], "error": last}


def cmd_plan(args):
    d = load_variants()
    todo = pending(d)
    total = sum(it.get("size", 0) for _, it, _ in todo)
    print(f"Biến thể đã ghi: {len(d.get('items', {}))} | cần upload: {len(todo)}"
          f" ({total/1048576:.1f} MB) | nguồn: {SRC_DIR.name}/")
    for uid, it, p in todo[:10]:
        print(f"  + thumbs/{it['key'].split('/', 1)[1]} ({it['size']/1024:.1f} KB)"
              f"{'' if p.exists() else '  ⚠ thiếu file local'}")
    if len(todo) > 10:
        print(f"  … và {len(todo)-10} biến thể khác")
    return 0


def cmd_upload(args):
    c = r2.cfg()
    if not r2.have_creds(c):
        print("SKIP: thiếu R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY.")
        print("  Đã thử các file cấu hình sau (thứ tự ưu tiên):")
        print(r2.env_paths_text())
        print("  → xem docs/R2-SETUP.md (hoặc set R2_ENV_FILE trỏ tới file có thật).")
        return 2
    d = load_variants()
    todo = [x for x in pending(d) if x[2].exists()]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print("Không có gì để upload (mọi biến thể đã live, hoặc thiếu file local).")
        return 0
    nbytes = sum(it.get("size", 0) for _, it, _ in todo)
    print(f"Upload {len(todo)} biến thể ({nbytes/1048576:.1f} MB) → {c['bucket']}/thumbs/ …")
    items = d.setdefault("items", {})
    ok = fail = 0
    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(upload_one, it, p): (uid, it) for uid, it, p in todo}
        for n, fut in enumerate(cf.as_completed(futs), 1):
            uid, it = futs[fut]
            r = fut.result()
            if r["ok"]:
                ok += 1
                done += it.get("size", 0)
                it["live"] = True
                it["uploaded_sha256"] = r["sha256"]
                it["etag"] = r["etag"]
            else:
                fail += 1
                print(f"  ✗ {r['key']}: {r['error']}", file=sys.stderr)
            if n % 50 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} · {done/1048576:.1f} MB · lỗi {fail}")
                save_variants(d)                    # lưu dần để resume
    save_variants(d)
    live = sum(1 for it in items.values() if it.get("live"))
    print(f"XONG: {ok} upload, {fail} lỗi. Live: {live}/{len(items)}."
          f" → chạy: python3 tools/build_index.py")
    return 0 if fail == 0 else 1


def cmd_verify(args):
    d = load_variants()
    live = [(uid, it) for uid, it in sorted(d.get("items", {}).items()) if it.get("live")]
    if not live:
        print("Chưa có biến thể nào live.")
        return 1
    if args.sample and args.sample < len(live):
        live = random.sample(live, args.sample)
    base = r2.cfg()["base"]
    bad = 0
    for uid, it in live:
        status, hdrs, _ = r2.s3_request("HEAD", it["key"])
        size = hdrs.get("Content-Length") or hdrs.get("content-length")
        ok = status == 200 and (not size or int(size) == it.get("size"))
        bad += 0 if ok else 1
        print(f"  {'OK ' if ok else 'FAIL'} {base}/{it['key']} ({size} B)")
    print(f"Verify: {len(live)-bad}/{len(live)} OK")
    return 0 if bad == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--upload", action="store_true")
    g.add_argument("--verify", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--sample", type=int)
    r2.load_env()  # r2_upload.py only calls load_env() in its own main(); importers must call it
    args = ap.parse_args(argv)
    if args.plan:
        return cmd_plan(args)
    if args.upload:
        return cmd_upload(args)
    return cmd_verify(args)


if __name__ == "__main__":
    sys.exit(main())
