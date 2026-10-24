---
name: Rad Verify
description: >-
  Cổng kiểm chứng repo Rad: chọn cổng nào chạy cho lesson.md, images/,
  index.html, README.md, BACKLOG.md hoặc tools/, đọc VERIFY PASS 5/5, và quyết
  định commit hay dừng. Dùng trước commit/báo "xong", sau pull/merge, hoặc khi
  verify_all báo FAIL/PARTIAL.
---

# Rad Verify — 5/5

Chạy đúng cổng, đọc đúng số, chỉ commit khi `VERIFY PASS 5/5`.

Ngoài phạm vi: nội dung y khoa (6 mục, nguồn, ảnh) → `medical-lesson-library`;
audit chỉ đọc → `verify_all.py --dry-run`; tranh luận chuyên môn → người thật.

Phạm vi thay đổi: `git status --short` + `git diff --name-only`.

## Bảng quyết định

| Thay đổi | Cổng bắt buộc |
|---|---|
| `*/lesson.md` mới/sửa | `check_duplicates.py` trước → `verify_all.py` |
| `*/images/**`, `*/sources.md` | `verify_all.py` + đọc CREDITS của bài |
| `index.html` | `verify_all.py`; xem `index_cards`, `lessons_missing_card` |
| `README.md`, `BACKLOG.md` | `verify_all.py`; xem `lessons_total`, `backlog_*` |
| `tools/**` | chạy script trên ≥5 bài mẫu + `verify_all.py` |
| chỉ docs/AGENTS | `git diff --stat`; `verify_all.py --only lint` nếu chạm bài |

## Chạy

```sh
python3 tools/verify_all.py
python3 tools/verify_all.py --offline   # chỉ khi mất mạng thật
python3 tools/verify_all.py --only selfcheck,lint
python3 tools/verify_all.py --dry-run   # audit, không ghi log
python3 tools/selfcheck.py <slug>       # một bài, khi đang sửa
```

Trước khi sửa: đọc dòng cuối `tools/verify_log.jsonl` để biết baseline. Chưa có
baseline thì chạy `--dry-run --offline` và ghi lại kết quả.

Bằng chứng: `tools/verify_report.json` (lượt gần nhất) và
`tools/verify_log.jsonl` (1 dòng/lượt).

## Điều kiện PASS

1. Exit 0 và dòng `VERIFY PASS` **5/5**: selfcheck, lint, mermaid, authors, index.
2. `index_parity_delta = 0`, `lessons_missing_card = 0`, `images_referenced_uncredited = 0`.
3. Mọi số trong báo cáo lấy từ report/log; ghi cả `selfcheck_warnings` (hiện 15 legacy).
4. `--only` chỉ được báo `PARTIAL PASS`, không được gọi là PASS toàn phần.
5. `--offline` chỉ khi mất mạng thật; ghi rõ số PMCID chưa xác minh.

## Khi FAIL

| Cổng | Việc |
|---|---|
| selfcheck | Sửa bài; chỉ sửa script khi script sai, ghi lý do, chạy lại toàn repo |
| lint | Sửa frontmatter/bảng/link; đọc warnings, không bỏ qua mù |
| mermaid | `fix_mermaid.py` rồi `--check`; vẫn lỗi thì viết lại hoặc bỏ sơ đồ |
| authors | Sửa theo `authorString` của PMCID; không chắc thì `Tạp chí Năm (PMCID)` không kèm tên |
| index | Thêm/sửa card + thumbnail; không sửa folder cho khớp card |
| mạng | `--offline`, ghi rõ số PMCID chưa xác minh |

Luật cứng: commit chỉ khi 5/5; sửa ngưỡng test chỉ khi test sai và có lý do;
`--offline` chỉ khi mất mạng thật.

## Chỉ số cần theo dõi (không tự chặn)

`images_referenced_uncredited` phải 0; `images_unreferenced_uncredited` kỳ vọng
0 (nếu >0: credit hoặc xóa); `backlog_duplicate_ids` >0 thì sửa;
`selfcheck_warnings` tăng thì điều tra. Chi tiết: `references/metrics.md`.

## Mẫu báo cáo

```text
verify: PASS 5/5 (selfcheck 0.4s · lint 0.7s · mermaid 0.3s · authors 0.6s · index)
parity index +0 · 515 bài / 515 card · chờ viết 112 · ID trùng 3
selfcheck warn: 15 bài legacy thiếu ma trận 2 cột
lệch so lượt trước: +2 bài (kỳ vọng +2), parity 0
```
