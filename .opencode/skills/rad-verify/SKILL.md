---
name: Rad Verify
description: >-
  Lớp quyết định cổng kiểm chứng cho repo Rad trước khi commit hoặc báo "xong":
  thay đổi nào thì chạy cổng nào, khi nào được coi là PASS, và bằng chứng nào
  phải tồn tại. Dùng khi vừa sửa lesson.md, images/, index.html, README.md,
  BACKLOG.md hoặc tools/ trong /home/openchamber/workspaces/Rad.
---

# Rad Verify — chạy cổng nào, khi nào

Mục tiêu: **không tuyên bố PASS khi chưa có bằng chứng**. Skill này chỉ là lớp
quyết định; luật nội dung (6 mục, ma trận, nguồn, ảnh) nằm ở skill toàn cục
`medical-lesson-library` + `AGENTS.md` + `PROMPT_SYNTHESIZER.md` — **không nhắc lại ở đây**.

## Khi nào dùng

- Trước mỗi commit trong repo Rad, và trước khi trả lời "đã xong".
- Sau khi pull/merge có thay đổi bài học, ảnh, hub hoặc BACKLOG.
- Khi một cổng báo FAIL và cần quyết định sửa gì / dừng ở đâu.

## Không dùng khi

- Đang viết nội dung y khoa (dùng `medical-lesson-library`).
- Chỉ đọc/audit không sửa gì (chạy `python3 tools/verify_all.py --dry-run` là đủ).
- Tranh luận chuyên môn (cần người thật).

## Đầu vào

1. Phạm vi: `git diff --name-only` + `git status --short` (gồm cả file chưa track).
2. Baseline: dòng cuối `tools/verify_log.jsonl` (nếu có) — trước khi sửa repo đang PASS hay FAIL.
3. Bài đang chạm: slug `NNN-...` (để chạy cổng hẹp khi cần).

Nếu chưa biết baseline: chạy `python3 tools/verify_all.py --dry-run --offline`
và ghi lại kết quả trước khi kết luận bất cứ điều gì.

## Bảng quyết định

| Thay đổi | Cổng bắt buộc | Ghi chú |
|---|---|---|
| `*/lesson.md` mới/sửa | `check_duplicates.py <ID> "<tên>"` (trước) → `verify_all.py` | verify_all đã gồm selfcheck + lint + mermaid + author |
| `*/images/**` | `verify_all.py` + tự kiểm từng dòng CREDITS | license phải cụ thể; CC BY-NC-ND giữ nguyên bản |
| `*/sources.md` | `verify_all.py` (author-check) | tên tác giả chỉ ghi khi đã đối chiếu PMCID |
| `index.html` | `verify_all.py` | đọc chỉ số `index_cards`, `lessons_missing_card` |
| `README.md` | `verify_all.py` | kiểm ID lặp dòng bằng mắt (chưa có cổng) |
| `BACKLOG.md` | `verify_all.py` + đếm `backlog_waiting`, `backlog_duplicate_ids` | append ≤ 2, ID không trùng |
| `tools/**` | chạy script trên ≥ 5 bài mẫu + `verify_all.py` | sửa script không được nới ngưỡng để pass |
| chỉ docs/AGENTS | `git diff --stat` + lint nếu có chạm bài | không cần chạy author-check mạng |

## Lệnh

```sh
python3 tools/verify_all.py                 # đủ 4 cổng, ghi report + log
python3 tools/verify_all.py --offline       # khi mạng lỗi (phải ghi rõ trong báo cáo)
python3 tools/verify_all.py --only selfcheck,lint
python3 tools/verify_all.py --dry-run       # không ghi log (audit)
python3 tools/selfcheck.py 1403-...         # một bài, khi đang sửa
```

Bằng chứng: `tools/verify_report.json` (chi tiết lượt gần nhất) và
`tools/verify_log.jsonl` (1 dòng/lượt, đã gitignore).

## Điều kiện PASS

1. `verify_all.py` exit **0**, **5/5** (selfcheck, lint, mermaid, authors, **index**).
   `index` là parity folder ↔ card: `index_parity_delta == 0` và `lessons_missing_card == 0`.
2. Chạy **đủ** cổng: dòng `VERIFY PASS`, không phải `VERIFY PARTIAL PASS`. Lượt chỉ chạy
   `--only` không được báo là PASS toàn phần (log ghi `partial: true`).
3. Author-check chạy **online** (trừ khi mất mạng thật; khi đó ghi rõ số PMCID chưa xác minh).
4. Mọi ảnh **hiển thị trong lesson.md** có dòng trong `images/CREDITS.md` với license cụ thể + link gốc.
5. Mỗi câu trong báo cáo cuối đều có số liệu lấy từ report/log — không nói "PASS" chung chung.
6. `selfcheck` có thể in `SELFCHECK WARN ... legacy` (15 bài cũ thiếu ma trận 2 cột): phải
   chép nguyên số đó vào báo cáo, không im lặng coi như sạch.

## Khi FAIL

| Cổng FAIL | Việc phải làm |
|---|---|
| selfcheck | Sửa bài (thiếu mục/bảng/quiz/link/ảnh). Không sửa script trừ khi script sai — khi đó sửa script, ghi lý do, chạy lại toàn repo |
| lint | Sửa frontmatter/bảng/link; cảnh báo (warnings) thì đọc và quyết định, không bỏ qua mù |
| mermaid | `python3 tools/fix_mermaid.py` rồi `--check` lại; vẫn lỗi thì viết lại sơ đồ hoặc bỏ, không commit đồ thị hỏng |
| authors | Sai tên → sửa theo `authorString` của PMCID; không chắc → `Tạp chí Năm (PMCID)` không kèm tên. Không "sửa" bằng cách xóa PMCID |
| index | Thêm/sửa card + thumbnail cho đúng số bài; không sửa ngược folder cho khớp card |
| mạng | `--offline`, ghi "chưa xác minh N PMCID" vào báo cáo; vẫn được commit theo luật hiện hành |

**Không bao giờ**: commit khi cổng FAIL, force-push, sửa ngưỡng test để pass,
chạy `--offline` khi mạng vẫn tốt để né author-check.

## Chỉ số chưa phải cổng (ghi nhận, không tự chặn)

`verify_all` chỉ ghi, chưa fail: ảnh hiển thị thiếu dòng CREDITS
(`images_referenced_uncredited`), số ảnh không hiển thị (`images_unreferenced` — nguồn
composite/bản cũ, không phải lỗi), ID trùng trong BACKLOG (`backlog_duplicate_ids`),
Mermaid mới kiểm bằng regex (chưa có parser thật), parity README.

Quy tắc: nếu `images_referenced_uncredited` > 0, hoặc chỉ số xấu **hai lượt liên tiếp**,
báo người dùng ở dòng cuối báo cáo; đừng tự nới luật cũng đừng tự chặn pipeline.

## Mẫu báo cáo

```
verify: PASS 5/5 (selfcheck 0.4s · lint 0.7s · mermaid 0.3s · authors 0.6s · index)
parity index +0 · 515 bài / 515 card · chờ viết 112 · ID trùng 3
selfcheck warn: 15 bài legacy thiếu ma trận 2 cột
lệch so lượt trước: +2 bài (kỳ vọng +2), parity 0
```

## Anti-patterns

- Chạy `selfcheck.py <một bài>` rồi nói "toàn repo PASS".
- Đọc log cũ rồi khẳng định lượt này PASS khi chưa chạy.
- Dùng `--offline` mặc định để nhanh.
- Sửa bài mẫu vàng hoặc hạ ngưỡng selfcheck cho khớp bài đang viết.
- Bỏ qua `index_parity_delta` vì "hub sửa tay vẫn đúng".
