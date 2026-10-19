#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_duplicates.py — Chặn viết bài trùng (ID hoặc chủ đề).

Vì sao: BACKLOG phình to khiến model dễ bỏ sót khi đối chiếu bằng mắt.
Script này kiểm TẤT ĐỊNH trên toàn bộ lesson.md hiện có.

Dùng:
    python3 tools/check_duplicates.py 543 "Viêm phổi hít sặc ở trẻ"
    python3 tools/check_duplicates.py 543            # chỉ kiểm ID

Exit:
    0 = không trùng (được viết)
    1 = TRÙNG ID hoặc tiêu đề quá giống (phải đổi)
"""
import sys, glob, re, os, itertools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = set("và của các ở trong cho với hay là một những khi do từ về the of and in to for a an "
           "bệnh hội chứng tổn thương hình ảnh chẩn đoán".split())


def load():
    out = []
    for f in glob.glob(os.path.join(ROOT, "*/lesson.md")):
        try:
            t = open(f, encoding="utf-8").read()
        except Exception:
            continue
        m = re.search(r'^unit_id:\s*"?([0-9]+)"?', t, re.M)
        h = re.search(r'^#\s+(.+)$', t, re.M)
        loc = re.search(r'^anatomical_location:\s*"?(.+?)"?\s*$', t, re.M)
        pat = re.search(r'^primary_pattern:\s*"?(.+?)"?\s*$', t, re.M)
        if not (m and h):
            continue
        title = re.sub(r'^\d+\s*[—\-–]\s*', '', h.group(1)).strip()
        out.append({
            "id": m.group(1),
            "folder": os.path.basename(os.path.dirname(f)),
            "title": title,
            "loc": (loc.group(1) if loc else "").lower(),
            "pat": (pat.group(1) if pat else "").lower(),
        })
    return out


def toks(s):
    s = re.sub(r'^\s*\d+\s*[—\-–]\s*', '', s)
    return {w for w in re.findall(r'[0-9a-zà-ỹ]+', s.lower())
            if w not in STOP and len(w) > 2}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    new_id = argv[0].strip()
    title = " ".join(argv[1:]).strip()
    if not re.fullmatch(r'\d{3,4}', new_id):
        print("⚠️  ID '%s' không phải 3–4 chữ số." % new_id)

    lessons = load()
    fails, warns = [], []

    # 1) trùng ID (folder hoặc unit_id)
    for L in lessons:
        if L["id"] == new_id or L["folder"].startswith(new_id + "-"):
            fails.append("ID %s đã tồn tại: %s" % (new_id, L["folder"]))

    # 2) tiêu đề tương đồng
    if title:
        a = toks(title)
        sims = []
        for L in lessons:
            b = toks(L["title"])
            if not a or not b:
                continue
            j = len(a & b) / len(a | b)
            if j >= 0.45:
                sims.append((j, L))
        sims.sort(reverse=True)
        for j, L in sims:
            msg = "%.2f | %s — %s" % (j, L["id"], L["title"][:90])
            (fails if j >= 0.62 else warns).append(msg)

        # 3) cùng vùng + cùng mẫu hình
        for L in lessons:
            if L["loc"] and L["pat"] and L["loc"] in title.lower() and L["pat"] in title.lower():
                warns.append("cùng vùng + mẫu hình với %s (%s)" % (L["id"], L["title"][:70]))

    print("🔎 check_duplicates — %d bài hiện có" % len(lessons))
    print("   ID đề xuất: %s | tiêu đề: %s" % (new_id, title or "(không đưa)"))
    if fails:
        print("\n❌ TRÙNG — phải đổi trước khi viết:")
        for x in fails:
            print("   -", x)
        print("\n→ Nếu chủ đề đã được phủ: NÂNG CẤP bài cũ thay vì tạo bài mới.")
        return 1
    if warns:
        print("\n⚠️  Gần giống (kiểm tra thủ công xem có thực sự khác không):")
        for x in warns:
            print("   -", x)
    print("\n✅ Không trùng ID/chủ đề — được phép viết.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
