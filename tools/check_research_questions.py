#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_research_questions.py — cổng kiểm mục 7 (bản nháp, CHƯA nối verify_all).

Kiểm:
  - có heading `## 7. Câu hỏi nghiên cứu & điểm chưa đồng thuận (tính đến MM/YYYY)`;
  - 2–3 mục, mỗi mục bắt đầu `**[Tranh cãi|Khoảng trống|Khác biệt thực hành]`;
  - mỗi mục có `Nguồn:` và ≥1 PMCID/DOI/URL;
  - chặn câu rỗng ("cần thêm nghiên cứu", "chưa có nghiên cứu nào") nếu không kèm nguồn.

Dùng:
    python3 tools/check_research_questions.py            # toàn repo (bài có mục 7)
    python3 tools/check_research_questions.py 1418 3200  # vài ID
    python3 tools/check_research_questions.py --strict   # bài thiếu mục 7 = FAIL

Exit 0 = PASS; 1 = FAIL.
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD = re.compile(r"^##\s*7\.\s*Câu hỏi nghiên cứu.*?\(tính đến\s*(\d{1,2}/\d{4})\)", re.I | re.M)
ITEM = re.compile(r"^\s*(\d+)\.\s*\*\*\[(Tranh cãi|Khoảng trống|Khác biệt thực hành)\]", re.M)
SRC = re.compile(r"\*\*Nguồn:\*\*|Nguồn:")
CIT = re.compile(r"PMC\d+|10\.\d{4,9}/[^\s)]+|https?://")
BANNED = re.compile(r"(cần thêm nghiên cứu|chưa có nghiên cứu nào|cần nghiên cứu thêm)", re.I)


def check(path):
    t = open(path, encoding="utf-8").read()
    m = HEAD.search(t)
    if not m:
        return ["thiếu heading mục 7 đúng mẫu"]
    errs = []
    start = m.end()
    nxt = re.search(r"^##\s", t[start:], re.M)
    body = t[start:start + nxt.start()] if nxt else t[start:]
    items = list(ITEM.finditer(body))
    if not (2 <= len(items) <= 3):
        errs.append(f"có {len(items)} mục (cần 2–3)")
    for i, it in enumerate(items):
        b = body[it.end(): items[i + 1].start() if i + 1 < len(items) else len(body)]
        if not SRC.search(b):
            errs.append(f"mục {it.group(1)} thiếu Nguồn:")
        if not CIT.search(b):
            errs.append(f"mục {it.group(1)} không có PMCID/DOI/URL")
        bm = BANNED.search(b)
        if bm:
            errs.append(f"mục {it.group(1)} dùng câu rỗng: “{bm.group(0)}”")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--strict", action="store_true", help="bài không có mục 7 → FAIL")
    a = ap.parse_args(argv)
    files = []
    if a.ids:
        for i in a.ids:
            g = glob.glob(os.path.join(ROOT, f"{i}-*", "lesson.md"))
            files += g
    else:
        files = glob.glob(os.path.join(ROOT, "*/lesson.md"))
    total = ok = 0
    for f in sorted(files):
        t = open(f, encoding="utf-8").read()
        if not HEAD.search(t):
            if a.strict:
                print(f"FAIL {os.path.basename(os.path.dirname(f))}: thiếu mục 7")
                total += 1
            continue
        total += 1
        errs = check(f)
        if errs:
            print(f"FAIL {os.path.basename(os.path.dirname(f))}: " + "; ".join(errs))
        else:
            ok += 1
    print(f"RESEARCH {'PASS' if ok == total else 'FAIL'}: {ok}/{total} bài có mục 7 hợp lệ")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
