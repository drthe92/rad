#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cdn.py — tra ảnh local sang URL Cloudflare R2 nếu đã có trong manifest.

Manifest: `tools/r2_manifest.json` do `tools/r2_upload.py --upload` ghi:
    {"base": "https://img.matcauvong.com", "files": {"<slug>/images/<file>": {...}}}

Dùng:
    from cdn import public_url
    public_url("020-not-phoi/images/x.jpg") -> "https://img.matcauvong.com/020-not-phoi/images/x.jpg" | None

Không có manifest / ảnh chưa upload → trả None để builder giữ đường dẫn local.
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "r2_manifest.json"
_cache = None


def load():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            _cache = {"base": os.environ.get("R2_PUBLIC_BASE", ""), "files": {}}
    return _cache


def public_url(local):
    """local: 'slug/images/file' hoặc '/slug/images/file'. Trả URL CDN hoặc None."""
    if not local:
        return None
    key = local.lstrip("/")
    m = load()
    base = (m.get("base") or "").rstrip("/")
    if base and key in m.get("files", {}):
        return f"{base}/{key}"
    return None


def rewrite_images(html, slug):
    """Đổi src="images/..." (trang /<slug>/) sang CDN nếu manifest có."""
    def repl(m):
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        key = src.lstrip("/")
        if not key.startswith(f"{slug}/"):
            key = f"{slug}/{key}"
        url = public_url(key)
        return f'src="{url}"' if url else m.group(0)
    return re.sub(r'src="([^"]+)"', repl, html)
