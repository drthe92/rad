#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_all.py — Một cửa duy nhất: chạy các cổng kiểm chứng + ghi log giữa các lượt.

Vì sao: worker chạy 4 script rời (selfcheck / lint / mermaid / author) nhưng không
lưu lại "lượt này đã chạy cổng nào, kết quả gì" → không đo được độ lệch giữa các
lượt (bài tăng mà card index không tăng, PMCID không tra được, cổng bị bỏ qua).

Script này KHÔNG thêm luật nội dung: nó gọi đúng 4 cổng sẵn có + kiểm parity hub
(folder ↔ card index), cộng vài chỉ số đối chiếu (BACKLOG, ảnh) để theo dõi xu hướng.
`--only` chạy một phần → in PARTIAL PASS và ghi `partial: true` vào log.

Dùng:
    python3 tools/verify_all.py               # chạy đủ, ghi log + report
    python3 tools/verify_all.py --offline     # author-check chỉ dùng cache
    python3 tools/verify_all.py --dry-run     # không ghi file
    python3 tools/verify_all.py --only selfcheck,lint

Exit code:
    0 = mọi cổng được chạy đều PASS (kể cả parity khi chạy đủ)
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
ALL_CHECKS = list(GATES) + ["index"]


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

    images, orphan, uncredited = 0, 0, 0
    for d in dirs:
        img_dir = os.path.join(ROOT, d, "images")
        if not os.path.isdir(img_dir):
            continue
        credits = os.path.join(img_dir, "CREDITS.md")
        credit_txt = ""
        if os.path.exists(credits):
            credit_txt = open(credits, encoding="utf-8").read()
        lesson_path = os.path.join(ROOT, d, "lesson.md")
        lesson_txt = ""
        if os.path.exists(lesson_path):
            lesson_txt = open(lesson_path, encoding="utf-8").read()
        referenced = set(re.findall(
            r"images/([^)\"'\s]+\.(?:jpg|jpeg|png|webp|gif))", lesson_txt, re.I))
        for f in os.listdir(img_dir):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                continue
            images += 1
            if f not in referenced:
                orphan += 1          # không hiển thị (nguồn composite, bản cũ/đổi tên)
            elif f not in credit_txt:
                uncredited += 1      # ĐANG hiển thị mà CREDITS không có tên → cần xem

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
        "images_unreferenced": orphan,
        "images_referenced_uncredited": uncredited,
    }


def run_index(m):
    """Parity hub ↔ folder là điều kiện PASS (rad-verify), không chỉ là chỉ số."""
    ok = m["index_parity_delta"] == 0 and m["lessons_missing_card"] == 0
    msg = ("delta=%+d, bài thiếu card=%d, card thừa=%d"
           % (m["index_parity_delta"], m["lessons_missing_card"],
              max(0, m["index_parity_delta"])))
    return {"name": "index", "exit": 0 if ok else 1, "pass": ok,
            "seconds": 0.0, "tail": [msg]}


def main(argv):
    offline = "--offline" in argv
    dry = "--dry-run" in argv
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            print("--only cần danh sách cổng, vd: --only selfcheck,lint")
            return 2
        only = [x.strip() for x in argv[i + 1].split(",") if x.strip()]
    unknown = [a for a in argv if a.startswith("--") and
               a not in ("--offline", "--dry-run", "--only")]
    if unknown:
        print("Tham số không hỗ trợ:", ", ".join(unknown))
        return 2
    bad = [g for g in (only or []) if g not in ALL_CHECKS]
    if bad:
        print("Cổng không tồn tại:", ", ".join(bad), "| có:", ", ".join(ALL_CHECKS))
        return 2

    commit = git("rev-parse", "--short", "HEAD")
    if not commit:
        print("Không phải git repo (hoặc chưa có commit) — không ghi log.")
        return 2
    dirty = len([l for l in git("status", "--porcelain").splitlines() if l.strip()])

    t0 = time.time()
    m = metrics()
    results = []
    for name in (only or list(GATES)):
        if name == "index":
            results.append(run_index(m))
            continue
        extra = ("--offline",) if (name == "authors" and offline) else ()
        results.append(run_gate(name, extra))
    if only is None or "index" not in only:
        results.append(run_index(m))   # parity luôn được kiểm

    requested = [r["name"] for r in results]
    partial = only is not None and set(only) != set(GATES)
    passed = sum(1 for r in results if r["pass"])
    ok = passed == len(results)
    duration = round(time.time() - t0, 1)

    label = "FAIL" if not ok else ("PARTIAL PASS" if partial else "PASS")
    print(f"VERIFY {label} ({passed}/{len(results)}: {', '.join(requested)})"
          f" — {m['lessons_total']} bài, {m['index_cards']} card,"
          f" {m['backlog_waiting']} chờ viết")
    for r in results:
        print(f"  {r['name']:<10} {'PASS' if r['pass'] else 'FAIL':<4} {r['seconds']:>5}s")
        if not r["pass"]:
            for line in r["tail"][-6:]:
                print("     ", line)
    print(f"  chỉ số: parity index {m['index_parity_delta']:+d},"
          f" ảnh hiển thị thiếu credit {m['images_referenced_uncredited']}"
          f"/{m['images_total']} (không hiển thị: {m['images_unreferenced']}),"
          f" BACKLOG ID trùng: {len(m['backlog_duplicate_ids'])}")
    if dirty:
        print(f"  lưu ý: working tree có {dirty} file thay đổi (log vẫn ghi).")

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "commit": commit,
        "dirty_files": dirty,
        "offline_authors": offline,
        "pass": ok,
        "partial": partial,
        "gates_requested": requested,
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
