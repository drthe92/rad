#!/usr/bin/env python3
"""Vòng tự kiểm trước commit (Self-Correction Loop — chống Model Lazy).
Chạy: python3 tools/selfcheck.py [slug...]  (mặc định: mọi folder NNN-/NNNN-)
Exit 0 = pass hết; exit 1 = có lỗi cần sửa trước khi commit.
Cảnh báo (không chặn): LEGACY_MATRIX — bài cũ chưa có ma trận 2 cột Chốt vào/Chốt loại.
"""
import os, re, sys

FRONT = ["unit_id", "subspecialty", "anatomical_location",
         "primary_pattern", "tags", "certainty"]
HEADS = ["## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6."]

# Bài cũ viết trước khi ma trận 2 cột thành luật (2026-10). Không miễn 6 mục/quiz —
# chỉ miễn RIÊNG cột Chốt vào/Chốt loại. Mỗi lượt chạm bài nào thì nâng cấp bài đó
# rồi xoá khỏi danh sách này (selfcheck sẽ nhắc khi thấy đã có ma trận).
LEGACY_MATRIX = {
    "011-tieu-thuy-phoi",
    "051-tieu-phe-quan",
    "075-tran-dich-mang-tim",
    "101-protocol-bung",
    "110-giai-phau-bung",
    "115-khi-tu-do",
    "136-u-nang-tuy",
    "150-nang-than-Bosniak",
    "152-soi-nieu",
    "155-thuong-than-tinh-co",
    "160-bung-cap-GI",
    "401-phuong-thuc-mat",
    "410-giai-phau-hoc-mat",
    "485-khuc-xa-ly-liet-dieu-tiet-tre-mam-non",
    "648-hoi-chung-de-mac-wilms-tam-soat-nephroblastomatosis",
}
WARNINGS = []


def is_overview(slug):
    """Tổng quan = theo TÊN FOLDER, không phải vì bài có nhắc chữ 'tổng quan'
    (391/515 bài từng được miễn oan chỉ vì link tới bài tổng quan)."""
    return "tong-quan" in slug or "overview" in slug

def check(slug):
    errs = []
    lp = f"{slug}/lesson.md"
    if not os.path.exists(lp):
        return [f"{slug}: thiếu lesson.md"]
    with open(lp, encoding="utf-8") as f:
        t = f.read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        errs.append("thiếu frontmatter YAML")
    else:
        for f in FRONT:
            if not re.search(rf"^{f}:", m.group(1), re.M):
                errs.append(f"frontmatter thiếu {f}")
    overview = is_overview(slug)
    if not overview:
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
        # Ma trận đối chiếu: tìm ĐÚNG khối bảng có cột Chốt vào/Chốt loại
        # (bài có thể mở đầu bằng bảng bối cảnh — không được lấy rows[0] làm ma trận).
        def heads(block):
            return block[0].lower()

        matrix = [b for b in blocks
                  if ("rule-in" in heads(b) or "chốt vào" in heads(b))
                  and ("rule-out" in heads(b) or "chốt loại" in heads(b))]
        if not matrix:
            if slug in LEGACY_MATRIX:
                WARNINGS.append(f"{slug}: chưa có ma trận 2 cột (legacy — nâng cấp khi chạm bài)")
            elif not overview:
                errs.append("thiếu ma trận có đủ cột Chốt vào/Chốt loại")
        elif slug in LEGACY_MATRIX:
            WARNINGS.append(f"{slug}: đã có ma trận — xoá khỏi LEGACY_MATRIX")
    imgs = sorted(set(re.findall(r"images/(\S+?\.(?:jpg|jpeg|png|webp|gif))", t)))
    missing = [i for i in imgs if not os.path.exists(f"{slug}/images/" + i)]
    if missing:
        errs.append(f"ảnh thiếu: {missing}")
    if "<details" not in t and not overview:
        errs.append("thiếu quiz <details>")
    if not re.search(r"\d+\s*(mm|HU|ngày|tuần|tháng|năm|%|cm|mL|g/dL|mg/dL|U/L|mIU|IU)", t):
        errs.append("thiếu số liệu định lượng (mm/HU/ngày/tuần/tháng/năm/%)")
    cp = f"{slug}/images/CREDITS.md"
    if not os.path.exists(cp):
        errs.append("thiếu images/CREDITS.md")
    sp = f"{slug}/sources.md"
    if not os.path.exists(sp):
        errs.append("thiếu sources.md")
    for m in re.finditer(r"\]\(\.\./([^)]+)/lesson\.md\)", t):
        if not os.path.exists(m.group(1) + "/lesson.md"):
            errs.append(f"link gãy tới {m.group(1)}")
    for l in t.split("\n"):
        if "(dự kiến)" in l and "](../" in l:
            errs.append("nhãn (dự kiến) đi kèm link — flip sang (đã có) hoặc trỏ đúng bài")
            break
    return [f"{slug}: {e}" for e in errs]

def discover():
    """Mọi folder bài NNN- hoặc NNNN- (dải ID 4 chữ số là hợp lệ, không được bỏ sót)."""
    return sorted(d for d in os.listdir(".")
                  if os.path.isdir(d) and re.match(r"^\d{3,4}-", d))

def main():
    slugs = sys.argv[1:] or discover()
    slugs = [s.rstrip("/") for s in slugs]
    allerrs = []
    for s in slugs:
        allerrs += check(s)
    if allerrs:
        print("SELFCHECK FAIL:")
        for e in allerrs:
            print(" -", e)
        sys.exit(1)
    warn = "" if not WARNINGS else f"; {len(WARNINGS)} cảnh báo legacy"
    print(f"SELFCHECK PASS ({len(slugs)} bài{warn})")
    if WARNINGS:
        print("SELFCHECK WARN (không chặn commit):")
        for w in WARNINGS:
            print(" !", w)

if __name__ == "__main__":
    main()
