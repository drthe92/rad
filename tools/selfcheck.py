#!/usr/bin/env python3
"""Vòng tự kiểm trước commit (Self-Correction Loop — chống Model Lazy).
Chạy: python3 tools/selfcheck.py [slug...]  (mặc định: tất cả NNN-*)
Exit 0 = pass hết; exit 1 = có lỗi cần sửa trước khi commit.
"""
import glob, os, re, sys

FRONT = ["unit_id", "subspecialty", "anatomical_location",
         "primary_pattern", "tags", "certainty"]
HEADS = ["## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6."]

def check(slug):
    errs = []
    lp = f"{slug}/lesson.md"
    if not os.path.exists(lp):
        return [f"{slug}: thiếu lesson.md"]
    t = open(lp).read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        errs.append("thiếu frontmatter YAML")
    else:
        for f in FRONT:
            if not re.search(rf"^{f}:", m.group(1), re.M):
                errs.append(f"frontmatter thiếu {f}")
    is_overview = "tong-quan" in t  # bài tổng quan (001) được miễn khung 6 mục
    if not is_overview:
        idx = [t.find(h) for h in HEADS]
        if any(i < 0 for i in idx):
            errs.append("thiếu mục (đủ 6 mục 1-6)")
        elif idx != sorted(idx):
            errs.append("sai thứ tự 6 mục")
    rows = [l for l in t.split("\n") if l.startswith("|")]
    if not rows:
        errs.append("thiếu bảng ma trận")
    else:
        # kiểm từng khối bảng liên tục (cho phép nhiều bảng cỡ khác nhau)
        blocks, cur = [], []
        for l in t.split("\n"):
            if l.startswith("|"):
                cur.append(l)
            elif cur:
                blocks.append(cur); cur = []
        if cur:
            blocks.append(cur)
        for b in blocks:
            n = b[0].count("|")
            bad = [l[:50] for l in b if l.count("|") != n]
            if bad:
                errs.append(f"bảng lệch cột: {bad[0]}...")
                break
        head = rows[0].lower()
        if "rule-in" not in head and "chốt vào" not in head and not is_overview:
            errs.append("bảng thiếu cột Chốt vào/Chốt loại")
    imgs = sorted(set(re.findall(r"images/(\S+?\.(?:jpg|png))", t)))
    missing = [i for i in imgs if not os.path.exists(f"{slug}/images/" + i)]
    if missing:
        errs.append(f"ảnh thiếu: {missing}")
    if "<details" not in t and not is_overview:
        errs.append("thiếu quiz <details>")
    if not re.search(r"\d+\s*(mm|HU|ngày|tuần|tháng|năm|%|cm|mL|g/dL|mg/dL|U/L|mIU|IU)", t):
        errs.append("thiếu số liệu định lượng (mm/HU/ngày/tuần/tháng/năm/%)")
    if "Chiarenza" in t or "Snoeckx" in t or "Hellerhoff" in t or "Doc James" in t:
        pass  # có attribution trong text
    cp = f"{slug}/images/CREDITS.md"
    if not os.path.exists(cp):
        errs.append("thiếu images/CREDITS.md")
    sp = f"{slug}/sources.md"
    if not os.path.exists(sp):
        errs.append("thiếu sources.md")
    return [f"{slug}: {e}" for e in errs]

def main():
    slugs = sys.argv[1:] or sorted(glob.glob("[0-9][0-9][0-9]-*/"))
    slugs = [s.rstrip("/") for s in slugs]
    allerrs = []
    for s in slugs:
        allerrs += check(s)
    if allerrs:
        print("SELFCHECK FAIL:")
        for e in allerrs:
            print(" -", e)
        sys.exit(1)
    print(f"SELFCHECK PASS ({len(slugs)} bài)")

if __name__ == "__main__":
    main()
