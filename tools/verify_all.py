#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_all.py — Một cửa duy nhất: chạy các cổng kiểm chứng + ghi log giữa các lượt.

Vì sao: worker chạy 4 script rời (selfcheck / lint / mermaid / author) nhưng không
lưu lại "lượt này đã chạy cổng nào, kết quả gì" → không đo được độ lệch giữa các
lượt (bài tăng mà card index không tăng, PMCID không tra được, cổng bị bỏ qua).

Script này KHÔNG thêm luật nội dung: nó gọi đúng các cổng sẵn có, cộng thêm vài
chỉ số đối chiếu (index ↔ folder, BACKLOG, ảnh) để theo dõi xu hướng.

Dùng:
    python3 tools/verify_all.py               # chạy đủ, ghi log + report
    python3 tools/verify_all.py --offline     # author-check chỉ dùng cache
    python3 tools/verify_all.py --dry-run     # không ghi file
    python3 tools/verify_all.py --only selfcheck,lint

Exit code:
    0 = mọi cổng PASS
    1 = có ít nhất 1 cổng FAIL
    2 = không chạy được (thiếu git / sai tham số)
Ghi: tools/verify_log.jsonl    (1 dòng JSON/lượt, giữ 500 dòng mới nhất)
     tools/verify_report.json (chi tiết lượt gần nhất — bằng chứng để đọc lại)
"""
import json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "tools", "verify_log.jsonl")
REPORT = os.path.join(ROOT, "tools", "verify_report.json")
MAX_LINES = 500

GATES = {
    "selfcheck": ["tools/selfcheck.py"],
    "lint": ["tools/lint_repo.py"],
    "mermaid": ["tools/fix_mermaid.py", "--check"],
    "authors": ["tools/check_credits_authors.py"],
}


def run_gate(name, extra=()):
    cmd = [sys.executable] + GATES[name] + list(extra)
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()
    return {
        "name": name,
        "exit": p.returncode,
        "pass": p.returncode == 0,
        "seconds": round(time.time() - t0, 1),
        "tail": out[-15:],
    }


def git(*args):
    try:
        p = subprocess.run(["git"] + list(args), cwd=ROOT,
                           capture_output=True, text=True)
        return p.stdout.strip()
    except FileNotFoundError:
        return ""


def lessons():
    out = []
    for d in sorted(os.listdir(ROOT)):
        if os.path.isdir(os.path.join(ROOT, d)) and re.match(r"^\d{3,4}-", d):
            out.append(d)
    return out


def metrics():
    dirs = lessons()
    total = len(dirs)
    n3 = sum(1 for d in dirs if re.match(r"^\d{3}-", d))
    idx_path = os.path.join(ROOT, "index.html")
    cards = set()
    if os.path.exists(idx_path):
        txt = open(idx_path, encoding="utf-8").read()
        cards = set(re.findall(r'view\.html\?b=([^&"\']+)', txt))

    images, uncredited = 0, 0
    for d in dirs:
        img_dir = os.path.join(ROOT, d, "images")
        credits = os.path.join(img_dir, "CREDITS.md")
        credit_txt = ""
        if os.path.exists(credits):
            credit_txt = open(credits, encoding="utf-8").read()
        if not os.path.isdir(img_dir):
            continue
        for f in os.listdir(img_dir):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                continue
            images += 1
            # Chỉ số tham khảo: ảnh ghép ghi nguồn theo ảnh gốc nên có thể báo dư.
            if f not in credit_txt:
                uncredited += 1

    waiting, dup_ids = 0, []
    bl = os.path.join(ROOT, "BACKLOG.md")
    if os.path.exists(bl):
        seen = {}
        for line in open(bl, encoding="utf-8"):
            if not line.startswith("|") or "chờ viết" not in line:
                continue
            waiting += 1
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) > 1 and re.fullmatch(r"\d{3,4}", cols[1]):
                seen[cols[1]] = seen.get(cols[1], 0) + 1
        dup_ids = sorted(k for k, v in seen.items() if v > 1)

    return {
        "lessons_total": total,
        "lessons_3digit": n3,
        "lessons_4digit": total - n3,
        "index_cards": len(cards),
        "index_parity_delta": len(cards) - total,
        "lessons_missing_card": len([d for d in dirs if d not in cards]),
        "backlog_waiting": waiting,
        "backlog_duplicate_ids": dup_ids,
        "images_total": images,
        "images_uncredited_hint": uncredited,
    }


def main(argv):
    offline = "--offline" in argv
    dry = "--dry-run" in argv
    only = None
    for i, a in enumerate(argv):
        if a == "--only" and i + 1 < len(argv):
            only = [x.strip() for x in argv[i + 1].split(",") if x.strip()]
    unknown = [a for a in argv if a.startswith("--") and
               a not in ("--offline", "--dry-run", "--only")]
    if unknown:
        print("Tham số không hỗ trợ:", ", ".join(unknown))
        return 2
    bad = [g for g in (only or []) if g not in GATES]
    if bad:
        print("Cổng không tồn tại:", ", ".join(bad), "| có:", ", ".join(GATES))
        return 2

    commit = git("rev-parse", "--short", "HEAD")
    if not commit:
        print("Không phải git repo (hoặc chưa có commit) — không ghi log.")
        return 2
    dirty = len([l for l in git("status", "--porcelain").splitlines() if l.strip()])

    t0 = time.time()
    results = []
    for name in (only or list(GATES)):
        extra = ("--offline",) if (name == "authors" and offline) else ()
        results.append(run_gate(name, extra))

    m = metrics()
    passed = sum(1 for r in results if r["pass"])
    ok = passed == len(results)
    duration = round(time.time() - t0, 1)

    print(f"VERIFY {'PASS' if ok else 'FAIL'} ({passed}/{len(results)} cổng)"
          f" — {m['lessons_total']} bài, {m['index_cards']} card,"
          f" {m['backlog_waiting']} chờ viết")
    for r in results:
        print(f"  {r['name']:<10} {'PASS' if r['pass'] else 'FAIL':<4} {r['seconds']:>5}s")
        if not r["pass"]:
            for line in r["tail"][-6:]:
                print("     ", line)
    print(f"  chỉ số: parity index {m['index_parity_delta']:+d},"
          f" ảnh {m['images_total']} (chưa có tên trong CREDITS:"
          f" {m['images_uncredited_hint']}),"
          f" BACKLOG ID trùng: {len(m['backlog_duplicate_ids'])}")
    if dirty:
        print(f"  lưu ý: working tree có {dirty} file thay đổi (log vẫn ghi).")

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "commit": commit,
        "dirty_files": dirty,
        "offline_authors": offline,
        "pass": ok,
        "gates": {r["name"]: {"pass": r["pass"], "exit": r["exit"],
                              "seconds": r["seconds"]} for r in results},
        "duration_s": duration,
        **m,
    }

    if not dry:
        try:
            lines = []
            if os.path.exists(LOG):
                lines = open(LOG, encoding="utf-8").read().splitlines()
            lines = [l for l in lines if l.strip()][-MAX_LINES + 1:]
            lines.append(json.dumps(entry, ensure_ascii=False))
            with open(LOG, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            entry["gates_detail"] = {r["name"]: r["tail"] for r in results}
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except OSError as e:
            print("  ⚠️  không ghi được log/report:", e)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
