#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_backlog.py — Giữ BACKLOG.md gọn, chuyển ghi chú dài sang BACKLOG-archive.md.

Vì sao: BACKLOG.md từng phình tới ~566 KB (~188k token) vì mỗi dòng `xong` và mỗi
lượt lại ghi chú rất dài → worker đọc cả file mỗi lượt, tốn context và dễ bỏ sót
khi đối chiếu trùng.

Đặc điểm:
  - Hàng `chờ viết` → giữ nguyên trong BACKLOG.md (để xếp ưu tiên).
  - Hàng `xong`     → ghi chú ĐẦY ĐỦ append vào BACKLOG-archive.md,
                      trong BACKLOG.md chỉ giữ 1 dòng nén `| ID | chủ đề ngắn |`.
  - Nhật ký         → append vào archive, xóa khỏi BACKLOG.md.
  - **Idempotent**: chạy lại nhiều lần không mất dữ liệu, không nhân đôi
    (dedupe theo ID; archive chỉ append phần mới).
  - **--auto**: chỉ tách khi BACKLOG.md vượt ngưỡng (mặc định 120 KB) → dùng
    trong vòng lặp worker mỗi lượt mà gần như không tốn gì.

Dùng:
    python3 tools/split_backlog.py              # tách ngay (nếu có gì để tách)
    python3 tools/split_backlog.py --auto       # chỉ tách khi > --max-kb
    python3 tools/split_backlog.py --max-kb 150
    python3 tools/split_backlog.py --dry-run
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "BACKLOG.md")
ARCH = os.path.join(ROOT, "BACKLOG-archive.md")
DEFAULT_MAX_KB = 120

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
|---|---|---|---|---|"""

DONE_HEAD = """
## Danh mục đã xong (ID | chủ đề ngắn) — dùng đối chiếu trùng

| ID | Chủ đề |
|---|---|"""

ARCH_HEAD = """# BACKLOG — LƯU TRỮ (worker KHÔNG đọc file này)

> Chứa ghi chú đầy đủ của các bài đã `xong` + nhật ký vòng lặp.
> Chỉ để tra cứu lịch sử; không ảnh hưởng vận hành.
> File làm việc là `BACKLOG.md`.

## Ghi chú đầy đủ các bài đã xong

| # | ID đề xuất | Chủ đề | Vì sao quan trọng nhất | Trạng thái |
|---|---|---|---|---|"""

SEP = set("-:| ")


def is_row(l):
    return l.startswith("|") and l.endswith("|")


def cells(l):
    return [x.strip() for x in l.split("|")[1:-1]]


def is_sep(l):
    return is_row(l) and set(l) <= SEP


def parse_all(txt):
    """Quét TOÀN file (không phụ thuộc vị trí mục):
    - hàng 5 cột  → bảng chờ viết / xong
    - hàng 2 cột  → danh mục đã xong (nén)
    - sau '## Nhật ký' → diary
    """
    five, two, diary = [], [], []
    mode = None
    for l in txt.split("\n"):
        s = l.strip()
        if s.startswith("## Nhật ký"):
            mode = "d"
            continue
        if mode == "d":
            diary.append(l)
            continue
        if is_row(l) and not is_sep(l):
            c = cells(l)
            if not c or c[0] in ("#", "ID"):
                continue
            if len(c) == 5:
                five.append((c, l))
            elif len(c) == 2 and c[0].isdigit():
                two.append((c, l))
    return five, two, diary


def parse_rows(lines, ncols):
    out = []
    for l in lines:
        if is_row(l) and not is_sep(l):
            c = cells(l)
            if len(c) == ncols and c[0] not in ("#", "ID", "---") and not c[0].startswith("-"):
                out.append((c, l))
    return out


def parse_archive(txt):
    if not txt:
        return [], []
    lines = txt.split("\n")
    done, diary = [], []
    mode = None
    for l in lines:
        s = l.strip()
        if s.startswith("## Ghi chú đầy đủ"):
            mode = "done"; continue
        if s.startswith("## Nhật ký"):
            mode = "diary"; continue
        if mode == "done":
            done.append(l)
        elif mode == "diary":
            diary.append(l)
    return parse_rows(done, 5), diary


def short(s, n=140):
    s = s.strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def main(argv):
    auto = "--auto" in argv
    dry = "--dry-run" in argv
    max_kb = DEFAULT_MAX_KB
    for i, a in enumerate(argv):
        if a == "--max-kb" and i + 1 < len(argv):
            max_kb = int(argv[i + 1])

    src = open(SRC, encoding="utf-8").read()
    size_kb = len(src.encode()) / 1024
    if auto and size_kb <= max_kb:
        print("BACKLOG.md %.0f KB ≤ %d KB — không cần tách." % (size_kb, max_kb))
        return 0

    five, compact, diary = parse_all(src)
    pending = [(c, l) for c, l in five if not c[4].lower().startswith("xong")]
    new_done = [(c, l) for c, l in five if c[4].lower().startswith("xong")]
    arch_txt = open(ARCH, encoding="utf-8").read() if os.path.exists(ARCH) else ""
    arch_done, arch_diary = parse_archive(arch_txt)

    done_ids = {c[1] for c, _ in arch_done}
    compact_ids = {c[0] for c, _ in compact}

    keep_pending = pending

    # append phần mới vào archive (dedupe theo ID)
    added_done = [(c, l) for c, l in new_done if c[1] not in done_ids]
    # thêm dòng nén vào danh mục
    new_compact = []
    for c, _ in new_done:
        if c[1] not in compact_ids:
            new_compact.append("| %s | %s |" % (c[1], short(c[2])))
            compact_ids.add(c[1])

    new_diary = [l for l in diary if l.strip()]

    out = [HEADER]
    out += [l for _, l in keep_pending]
    out.append(DONE_HEAD)
    out += [l for _, l in compact]
    out += new_compact
    out.append("")

    arch = [ARCH_HEAD]
    arch += [l for _, l in arch_done]
    arch += [l for _, l in added_done]
    if arch_diary or new_diary:
        arch.append("")
        arch.append("## Nhật ký vòng lặp")
        arch += [l for l in arch_diary if l.strip()]
        arch += new_diary
    arch.append("")

    new_src = "\n".join(out).rstrip() + "\n"
    new_arch = "\n".join(arch).rstrip() + "\n"

    changed = new_src != src
    print("chờ viết: %d | xong mới: %d | archive thêm: %d | diary thêm: %d"
          % (len(keep_pending), len(new_done), len(added_done), len(new_diary)))
    print("BACKLOG.md: %.0f KB → %.0f KB" % (size_kb, len(new_src.encode()) / 1024))

    if dry:
        print("(--dry-run: không ghi)")
        return 0
    if not changed:
        print("Không có gì để tách.")
        return 0

    open(SRC, "w", encoding="utf-8").write(new_src)
    open(ARCH, "w", encoding="utf-8").write(new_arch)
    print("Đã ghi BACKLOG.md + BACKLOG-archive.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
