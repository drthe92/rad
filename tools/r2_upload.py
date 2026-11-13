#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r2_upload.py — đưa ảnh bài học lên Cloudflare R2 (S3 API), không cần aws-cli.

Vì sao: site GitHub Pages đã ~840 MB (ảnh ~640 MB), sát ngưỡng 1 GB. Ảnh chuyển
sang `img.matcauvong.com` (R2 + custom domain) để site nhẹ và tải nhanh hơn.

Đặc điểm:
  - SigV4 thuần Python (urllib + hmac), không phụ thuộc gói ngoài.
  - Key giữ nguyên cây: `<slug>/images/<file>` → `https://img.matcauvong.com/<slug>/images/<file>`.
  - Manifest `tools/r2_manifest.json` (sha256 + size + etag) để build biết ảnh nào đã có trên CDN.
  - Chạy lại chỉ upload ảnh mới/đổi (so sha256), có resume.
  - Không in khóa bí mật.

Cấu hình: biến môi trường hoặc file `~/.config/rad/r2.env` (ưu tiên file, không ghi đè env):
    R2_ACCOUNT_ID=...
    R2_ACCESS_KEY_ID=...
    R2_SECRET_ACCESS_KEY=...
    R2_BUCKET=rad-img
    R2_PUBLIC_BASE=https://img.matcauvong.com

Dùng:
    python3 tools/r2_upload.py --plan          # chỉ tính, không cần mạng
    python3 tools/r2_upload.py --upload        # upload ảnh mới/đổi
    python3 tools/r2_upload.py --upload --limit 5
    python3 tools/r2_upload.py --verify        # HEAD kiểm ảnh đã có
    python3 tools/r2_upload.py --verify --sample 50

Exit: 0 OK/SKIP; 1 lỗi; 2 thiếu cấu hình khi cần.
"""
import argparse
import concurrent.futures as cf
import hashlib
import hmac
import json
import mimetypes
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "r2_manifest.json"
ENV_FILE = Path(os.environ.get("R2_ENV_FILE", Path.home() / ".config" / "rad" / "r2.env"))
UA = "rad-r2-uploader/1.0"
CACHE_CONTROL = "public, max-age=31536000, immutable"
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml"}


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


def cfg():
    return {
        "account": os.environ.get("R2_ACCOUNT_ID", "").strip(),
        "ak": os.environ.get("R2_ACCESS_KEY_ID", "").strip(),
        "sk": os.environ.get("R2_SECRET_ACCESS_KEY", "").strip(),
        "bucket": os.environ.get("R2_BUCKET", "rad-img").strip(),
        "base": os.environ.get("R2_PUBLIC_BASE", "https://img.matcauvong.com").strip().rstrip("/"),
    }


def have_creds(c):
    return bool(c["account"] and c["ak"] and c["sk"])


# ── SigV4 ───────────────────────────────────────────────────────────────────
def _hmac(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret, datestamp, region, service):
    k = _hmac(("AWS4" + secret).encode("utf-8"), datestamp)
    for msg in (region, service, "aws4_request"):
        k = _hmac(k, msg)
    return k


def _canonical_uri(path):
    return urllib.parse.quote(path, safe="/~")


def sign_v4(method, host, path, headers, payload_hash, ak, sk, region, service, amzdate):
    """Ký SigV4; headers là dict đã có host + x-amz-*. Trả Authorization + signed headers."""
    datestamp = amzdate[:8]
    signed_headers = ";".join(sorted(headers))
    canonical_headers = "".join(f"{k}:{str(headers[k]).strip()}\n" for k in sorted(headers))
    canonical_request = "\n".join([
        method, _canonical_uri(path), "", canonical_headers, signed_headers, payload_hash,
    ])
    scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amzdate, scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])
    signature = hmac.new(_signing_key(sk, datestamp, region, service),
                         string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    auth = (f"AWS4-HMAC-SHA256 Credential={ak}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}")
    return auth, signed_headers


def s3_request(method, key="", body=b"", extra_headers=None, timeout=90):
    c = cfg()
    host = f"{c['account']}.r2.cloudflarestorage.com"
    amzdate = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload_hash = hashlib.sha256(body).hexdigest()

    headers = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amzdate,
    }
    for k, v in (extra_headers or {}).items():
        headers[k.lower()] = v

    path = f"/{c['bucket']}/{key}" if key else f"/{c['bucket']}"
    auth, _ = sign_v4(method, host, path, headers, payload_hash,
                      c["ak"], c["sk"], "auto", "s3", amzdate)
    headers["authorization"] = auth

    url = f"https://{host}/{_canonical_uri(key)}" if key else f"https://{host}/"
    req = urllib.request.Request(url, data=body if method in ("PUT", "POST") else None,
                                 method=method, headers=headers)
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


# ── manifest & files ────────────────────────────────────────────────────────
def load_manifest():
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"base": cfg()["base"], "files": {}}


def save_manifest(m):
    m["base"] = cfg()["base"]
    m["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(MANIFEST)


def iter_images():
    for p in sorted(ROOT.iterdir()):
        if not p.is_dir() or not p.name[:1].isdigit():
            continue
        img = p / "images"
        if not img.is_dir():
            continue
        for f in sorted(img.iterdir()):
            if f.is_file() and f.suffix.lower() in MIME and f.name != "CREDITS.md":
                yield p.name, f


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def plan(limit=None):
    m = load_manifest()
    known = m.get("files", {})
    todo, skip, total = [], 0, 0
    bytes_todo = 0
    for slug, f in iter_images():
        key = f"{slug}/images/{f.name}"
        total += 1
        sha = sha256_file(f)
        rec = known.get(key)
        if rec and rec.get("sha256") == sha:
            skip += 1
            continue
        size = f.stat().st_size
        todo.append({"key": key, "path": f, "sha256": sha, "size": size})
        bytes_todo += size
        if limit and len(todo) >= limit:
            break
    return todo, skip, total, bytes_todo


def upload_one(item, attempts=3):
    key, path = item["key"], item["path"]
    body = path.read_bytes()
    sha = item["sha256"]
    assert hashlib.sha256(body).hexdigest() == sha
    ctype = MIME.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    last = None
    for i in range(attempts):
        status, hdrs, resp = s3_request(
            "PUT", key, body,
            {"content-type": ctype, "cache-control": CACHE_CONTROL,
             "x-amz-meta-sha256": sha},
        )
        if status in (200, 201):
            return {"ok": True, "key": key, "etag": (hdrs.get("ETag") or hdrs.get("etag") or "").strip('"'),
                    "sha256": sha, "size": len(body), "status": status}
        last = f"HTTP {status}: {resp[:200]!r}"
        if status not in (429, 500, 502, 503, 504):
            break
        time.sleep((2 ** i) + random.random())
    return {"ok": False, "key": key, "error": last}


def cmd_plan(args):
    todo, skip, total, nbytes = plan(args.limit)
    print(f"Ảnh trong repo: {total} | đã có trên CDN: {skip} | cần upload: {len(todo)}"
          f" ({nbytes/1048576:.1f} MB)")
    for it in todo[:10]:
        print(f"  + {it['key']} ({it['size']/1024:.0f} KB)")
    if len(todo) > 10:
        print(f"  … và {len(todo)-10} ảnh khác")
    return 0


def cmd_upload(args):
    c = cfg()
    if not have_creds(c):
        print("SKIP: thiếu R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY.")
        print(f"  → tạo {ENV_FILE} (xem hướng dẫn trong AGENTS.md / README-R2).")
        return 2 if args.strict else 0
    todo, skip, total, nbytes = plan(args.limit)
    if not todo:
        print(f"Không có gì để upload ({total} ảnh, tất cả đã có trong manifest).")
        return 0
    print(f"Upload {len(todo)} ảnh ({nbytes/1048576:.1f} MB) → {c['bucket']} …")
    m = load_manifest()
    files = m.setdefault("files", {})
    ok = fail = 0
    done_bytes = 0
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(upload_one, it): it for it in todo}
        for n, fut in enumerate(cf.as_completed(futs), 1):
            r = fut.result()
            if r["ok"]:
                ok += 1
                done_bytes += r["size"]
                files[r["key"]] = {"sha256": r["sha256"], "size": r["size"], "etag": r["etag"]}
            else:
                fail += 1
                print(f"  ✗ {r['key']}: {r['error']}", file=sys.stderr)
            if n % 25 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} · {done_bytes/1048576:.1f} MB · lỗi {fail}")
                save_manifest(m)  # lưu dần để resume
    save_manifest(m)
    print(f"XONG: {ok} upload, {fail} lỗi. Manifest: {MANIFEST.relative_to(ROOT)}")
    return 0 if fail == 0 else 1


def cmd_verify(args):
    m = load_manifest()
    keys = sorted(m.get("files", {}).keys())
    if not keys:
        print("Manifest rỗng — chưa upload gì.")
        return 1
    sample = args.sample or len(keys)
    if sample < len(keys):
        keys = random.sample(keys, sample)
    c = cfg()
    bad = 0
    for key in keys:
        status, hdrs, _ = s3_request("HEAD", key)
        ok = status == 200
        if ok and args.public:
            url = f"{c['base']}/{urllib.parse.quote(key)}"
            try:
                req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=30) as r:
                    ok = r.status == 200
            except Exception:
                ok = False
        if not ok:
            bad += 1
            print(f"  ✗ {key}: HTTP {status}")
    print(f"Kiểm {len(keys)} ảnh: {len(keys)-bad} OK, {bad} lỗi.")
    return 0 if bad == 0 else 1


def cmd_selftest(args):
    """Vector chính thức AWS SigV4 (get-vanilla) — bắt lỗi ký trước khi upload thật."""
    amzdate = "20150830T123600Z"
    headers = {"host": "example.amazonaws.com", "x-amz-date": amzdate}
    auth, signed = sign_v4(
        "GET", "example.amazonaws.com", "/", headers,
        hashlib.sha256(b"").hexdigest(),
        "AKIDEXAMPLE", "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        "us-east-1", "service", amzdate,
    )
    want = "5fa00fa31553b73ebf1942676e86291e8372ff2a2260956d9b8aae1d763fbf31"
    ok = auth.endswith("Signature=" + want)
    print(("SELFTEST OK" if ok else "SELFTEST FAIL") + f" (signed: {signed})")
    if not ok:
        print("  got:", auth.rsplit("Signature=", 1)[-1])
    return 0 if ok else 1


def main(argv=None):
    load_env()
    ap = argparse.ArgumentParser(description="Upload ảnh bài học lên Cloudflare R2")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--upload", action="store_true")
    g.add_argument("--verify", action="store_true")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--public", action="store_true", help="kiểm thêm URL công khai")
    ap.add_argument("--strict", action="store_true", help="thiếu cấu hình → exit 2")
    a = ap.parse_args(argv)
    if a.plan:
        return cmd_plan(a)
    if a.upload:
        return cmd_upload(a)
    if a.selftest:
        return cmd_selftest(a)
    return cmd_verify(a)


if __name__ == "__main__":
    raise SystemExit(main())
