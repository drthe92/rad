#!/usr/bin/env python3
"""Cài Pillow (cho tools/make_composite.py) mà KHÔNG cần pip / quyền root.

Môi trường repo có python3 nhưng thiếu pip, ensurepip, ImageMagick và không có sudo.
Script này tải wheel manylinux khớp đúng phiên bản Python + kiến trúc máy từ PyPI
rồi giải nén vào site-packages của user (mặc định ~/.local/lib/pythonX.Y/site-packages).

Chạy:  python3 tools/ensure_deps.py
Kiểm:  python3 -c "import PIL; print(PIL.__version__)"
Idempotent: nếu đã import được Pillow thì không tải lại (trừ khi --force).
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import sysconfig
import tempfile
import urllib.request
import zipfile

PYPI = "https://pypi.org/pypi/Pillow/json"


def platform_tags():
    """Trả về các mảnh cần có trong tên wheel theo kiến trúc máy."""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return ["x86_64"]
    if machine in ("aarch64", "arm64"):
        return ["aarch64"]
    raise SystemExit(f"Kiến trúc chưa hỗ trợ: {machine} — cài Pillow thủ công.")


def pick_wheel(version=None):
    with urllib.request.urlopen(PYPI, timeout=30) as r:
        meta = json.load(r)
    if version:
        with urllib.request.urlopen(f"https://pypi.org/pypi/Pillow/{version}/json", timeout=30) as r:
            meta = json.load(r)
    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    arches = platform_tags()
    files = meta["urls"]
    cands = [f for f in files
             if f["filename"].endswith(".whl")
             and tag in f["filename"]
             and "manylinux" in f["filename"]
             and any(a in f["filename"] for a in arches)]
    if not cands:
        raise SystemExit(f"Không tìm thấy wheel {tag} manylinux cho {arches}. "
                         f"Dùng --version hoặc cài thủ công.")
    return max(cands, key=lambda f: f["filename"])  # bản mới nhất khớp


def target_dir():
    try:
        return subprocess.check_output([sys.executable, "-m", "site", "--user-site"],
                                       text=True).strip()
    except Exception:
        return sysconfig.get_paths()["purelib"]


def has_pillow():
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Tải Pillow wheel và giải nén vào user site-packages")
    ap.add_argument("--version", help="phiên bản Pillow cụ thể (mặc định: mới nhất)")
    ap.add_argument("--target", help="thư mục đích (mặc định: user site-packages)")
    ap.add_argument("--force", action="store_true", help="tải lại dù đã import được Pillow")
    args = ap.parse_args()

    if has_pillow() and not args.force and not args.target:
        import PIL
        print(f"OK: Pillow {getattr(PIL, '__version__', '?')} đã có — không cần cài.")
        return

    wheel = pick_wheel(args.version)
    dest = args.target or target_dir()
    os.makedirs(dest, exist_ok=True)
    print(f"→ {wheel['filename']}")
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, wheel["filename"])
        urllib.request.urlretrieve(wheel["url"], path)
        with zipfile.ZipFile(path) as z:
            z.extractall(dest)
    print(f"→ giải nén vào {dest}")

    if args.target:
        print("Lưu ý: dùng --target thì phải đặt PYTHONPATH trỏ tới thư mục đó.")
        return
    try:
        import PIL
        print(f"OK: Pillow {PIL.__version__} sẵn sàng — chạy được tools/make_composite.py")
    except Exception as e:
        raise SystemExit(f"Cài xong nhưng import lỗi: {e}")


if __name__ == "__main__":
    main()
