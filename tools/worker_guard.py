#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
worker_guard.py — Khóa chống chồng lượt cho worker rad-backlog-autofill.

Vì sao: khóa kiểu "model tự đọc mtime rồi đoán" đã thất bại (15:00 ghi đè khóa
của 14:30 → 2 session chạy song song). Script này quyết định TẤT ĐỊNH.

Dùng:
    python3 tools/worker_guard.py acquire     # exit 0 = lấy được khóa; exit 3 = BUSY
    python3 tools/worker_guard.py release     # xóa khóa (best-effort)
    python3 tools/worker_guard.py status      # xem trạng thái

TTL mặc định 90 phút: khóa cũ hơn TTL coi như worker chết → cho lấy.
"""
import json, os, sys, time

LOCK = "/tmp/opencode/rad-worker.lock"
DEFAULT_TTL_MIN = 90


def age_min():
    try:
        st = os.stat(LOCK)
        return (time.time() - st.st_mtime) / 60.0
    except FileNotFoundError:
        return None


def acquire(ttl=DEFAULT_TTL_MIN):
    a = age_min()
    if a is not None and a < ttl:
        try:
            info = json.load(open(LOCK, encoding="utf-8"))
        except Exception:
            info = {}
        print("BUSY: worker khác đang chạy (khóa %.1f phút trước, TTL %d). DỪNG."
              % (a, ttl))
        if info:
            print("      lock=%s" % json.dumps(info, ensure_ascii=False))
        return 3
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    payload = {"pid": os.getpid(), "ts": int(time.time()),
               "iso": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    with open(LOCK, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    if a is None:
        print("OK: đã lấy khóa (không có khóa cũ).")
    else:
        print("OK: đã lấy khóa (khóa cũ %.1f phút > TTL %d → coi như worker chết)."
              % (a, ttl))
    return 0


def release():
    try:
        os.remove(LOCK)
        print("OK: đã xóa khóa.")
    except FileNotFoundError:
        print("OK: không có khóa để xóa.")
    return 0


def status():
    a = age_min()
    if a is None:
        print("Không có khóa (rảnh).")
    else:
        try:
            info = json.load(open(LOCK, encoding="utf-8"))
        except Exception:
            info = {}
        print("Khóa tồn tại: %.1f phút trước | %s" % (a, json.dumps(info, ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    ttl = DEFAULT_TTL_MIN
    for i, a in enumerate(sys.argv):
        if a == "--ttl" and i + 1 < len(sys.argv):
            ttl = int(sys.argv[i + 1])
    if cmd == "acquire":
        sys.exit(acquire(ttl))
    elif cmd == "release":
        sys.exit(release())
    elif cmd == "status":
        sys.exit(status())
    else:
        print(__doc__)
        sys.exit(2)
