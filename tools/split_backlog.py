#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_backlog.py — Giữ BACKLOG.md gọn, chuyển phần dài sang BACKLOG-archive.md.

Vì sao: BACKLOG.md từng phình tới ~566 KB (~188k token) vì mỗi dòng `xong` và mỗi
lượt lại ghi chú rất dài → worker đọc cả file mỗi lượt, tốn context và dễ bỏ sót
khi đối chiếu trùng (lost-in-the-middle).

Cách làm:
  - Hàng `chờ viết`  → giữ nguyên trong BACKLOG.md (cần để xếp ưu tiên).
  - Hàng `xong`      → chuyển ghi chú đầy đủ sang BACKLOG-archive.md,
                       chỉ giữ 1 dòng nén `| ID | chủ đề ngắn |` trong BACKLOG.md.
  - Nhật ký vòng lặp → chuyển sang BACKLOG-archive.md.

Dùng:
    python3 tools/split_backlog.py --dry-run   # xem trước
    python3 tools/split_backlog.py             # ghi file
"""
import re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "BACKLOG.md")
ARCH = os.path.join(ROOT, "BACKLOG-archive.md")

HEADER = """# BACKLOG — Khoảng trống kiến thức chưa có trong thư viện (tự mở rộng)

> Vòng lặp tự lấp đầy: mỗi turn lấy top 1–2 mục `chờ viết`, viết đúng chuẩn
> `AGENTS.md` + 4 cửa Argon, rồi flip thành `xong`.
> **Append tối đa 2 khoảng trống mới/lượt.**
> **Chống trùng (bắt buộc):** trước khi viết hoặc append, chạy
> `python3 tools/check_duplicates.py <ID> "<tên bài>"` — exit 0 mới được tiếp tục.
> Script kiểm: ID đã tồn tại (folder/`unit_id`), tiêu đề tương đồng, cùng vùng + mẫu hình.
> **KHÔNG đọc `BACKLOG-archive.md`** — đó chỉ là lưu trữ ghi chú dài + nhật ký.
> Tiêu chí xếp hạng: tần suất gặp lâm sàng > nguy cơ bỏ sót chết người > giá trị thi cử.
> Mỗi turn tối đa **2 bài** (giới hạn context + verify giấy phép ảnh từng bài).

## Hàng chờ viết (ưu tiên trên → dưới)

| # | ID đề xuất | Chủ đề | Vì sao quan trọng nhất | Trạng thái |
|---|---|---|---|---|
"""

DONE_HEAD = """
## Danh mục đã xong (ID | chủ đề ngắn) — dùng đối chiếu trùng

| ID | Chủ đề |
|---|---|
"""

ARCH_HEAD = """# BACKLOG — LƯU TRỮ (worker KHÔNG đọc file này)

> Chứa ghi chú đầy đủ của các bài đã `xong` + nhật ký vòng lặp.
> Chỉ để tra cứu lịch sử; không ảnh hưởng vận hành.
> File làm việc là `BACKLOG.md`.

## Ghi chú đầy đủ các bài đã xong

| # | ID đề xuất | Chủ đề | Vì sao quan trọng nhất | Trạng thái |
|---|---|---|---|---|
"""


def cell(s):
    return s.strip()


def short_topic(s, n=140):
    s = cell(s)
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def main(dry=False):
    txt = open(SRC, encoding="utf-8").read()
    lines = txt.split("\n")

    # tách nhật ký
    di = next((i for i, l in enumerate(lines) if l.strip().startswith("## Nhật ký")), None)
    body = lines if di is None else lines[:di]
    diary = [] if di is None else lines[di:]

    pending, done = [], []
    for l in body:
        if not (l.startswith("|") and l.endswith("|")):
            continue
        parts = l.split("|")
        # '' | c1 | c2 | c3 | c4 | c5 | ''  -> 7
        if len(parts) != 7:
            continue
        c = [cell(x) for x in parts[1:-1]]
        if c[0] in ("#", "---") or set(c[0]) <= set("-"):
            continue
        status = c[4].lower()
        (done if status.startswith("xong") else pending).append((c, l))

    out = [HEADER.rstrip("\n")]
    for _, l in pending:
        out.append(l)
    out.append(DONE_HEAD.rstrip("\n"))
    for c, _ in done:
        out.append("| %s | %s |" % (c[1], short_topic(c[2], 140)))
    out.append("")

    arch = [ARCH_HEAD.rstrip("\n")]
    for _, l in done:
        arch.append(l)
    arch.append("")
    arch.extend(diary)

    new_b = "\n".join(out).rstrip() + "\n"
    new_a = "\n".join(arch).rstrip() + "\n"

    print("chờ viết: %d | xong: %d" % (len(pending), len(done)))
    print("BACKLOG.md:        %7d → %7d bytes" % (len(txt.encode()), len(new_b.encode())))
    print("BACKLOG-archive:   %7d bytes" % len(new_a.encode()))
    if dry:
        print("(--dry-run: không ghi file)")
        return 0
    open(SRC, "w", encoding="utf-8").write(new_b)
    open(ARCH, "w", encoding="utf-8").write(new_a)
    print("Đã ghi BACKLOG.md + BACKLOG-archive.md")
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))
