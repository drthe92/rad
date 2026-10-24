---
name: Rad Backlog
description: >-
  Vòng lặp tự lấp đầy BACKLOG cho repo Rad: khóa chống chồng lượt, đồng bộ git,
  chọn 1–2 chủ đề, kiểm trùng, viết bài theo chuẩn, cập nhật hub/README/BACKLOG,
  verify rồi commit/push. Dùng khi chạy worker định kỳ hoặc khi được yêu cầu
  "viết bài tiếp theo trong BACKLOG" tại /home/openchamber/workspaces/Rad.
---

# Rad Backlog — một lượt worker

Đây là **thứ tự công việc**, không phải luật nội dung. Luật nội dung đọc từ:
`AGENTS.md` (quy ước bất biến), `PROMPT_SYNTHESIZER.md` (4 cửa Argon),
`templates/lesson-template.md` + `templates/gold-standard-lesson.md`,
và skill toàn cục `medical-lesson-library` (khung 6 mục, nguồn, ảnh, license).
Nếu skill toàn cục không được nạp, 3 file đầu vẫn đủ để làm đúng.

## 0. Khóa (bắt buộc, trước mọi việc khác)

```sh
python3 tools/worker_guard.py acquire
```

- Exit **0** → tiếp tục, và đặt nghĩa vụ **release ở mọi nhánh thoát**.
- Exit **3 (BUSY)** → **dừng ngay**, không đọc/ghi gì thêm, trả lời 1 dòng "BUSY, bỏ lượt".
- Cuối lượt, kể cả khi lỗi/dừng giữa đường:

```sh
python3 tools/worker_guard.py release
python3 tools/worker_guard.py status    # xác nhận đã nhả
```

## 1. Đồng bộ

```sh
cd /home/openchamber/workspaces/Rad
git status --short
```

**Cây sạch** → `git pull --rebase`, xong.

**Cây bẩn** — phải phân biệt *việc dở của worker bị cắt ngang* với *phiên khác đang sửa*:

```sh
# 1) File bẩn nào không thuộc phạm vi worker, hoặc vừa bị sửa < 10 phút?
now=$(date +%s)
git status --porcelain | awk '{print $2}' | while read -r f; do
  age=$(( now - $(stat -c %Y "$f" 2>/dev/null || echo "$now") ))
  case "$f" in
    [0-9][0-9][0-9]*-*/*|index.html|README.md|BACKLOG*.md|tools/*|.opencode/*) ;;
    *) echo "NGOÀI PHẠM VI: $f" ;;
  esac
  [ "$age" -lt 600 ] && echo "MỚI SỬA <10 phút: $f"
done
```

- Có dòng `NGOÀI PHẠM VI` hoặc `MỚI SỬA` → **KHÔNG stash, DỪNG**, release, báo rõ
  (khả năng cao là phiên khác đang sửa — đúng tình huống đã gặp 2026-10-24).
- Không có → đây là việc dở của lượt trước:

```sh
git stash push -u -m "interrupted-$(date +%s)"
STASH=$(git rev-parse stash@{0})   # ghi ref này vào nhật ký
git pull --rebase                  # cây đã sạch nên pull được
git stash pop                      # khôi phục NGAY, không để treo
```

- `git stash pop` conflict → **dừng**, để nguyên stash (không `drop`), release, báo.
- Conflict khi pull → **dừng**, release, báo 1 dòng. Không tự xóa file người khác.

> Không dùng `--autostash` thay cho bước trên: nó stash/pop ngầm, không phân biệt
> được việc dở với sửa đổi đang sống và không để lại ref để khôi phục khi conflict.

## 2. Đọc (ngân sách context)

Đọc: `AGENTS.md`, **đầu** `BACKLOG.md` (bảng hàng chờ), `PROMPT_SYNTHESIZER.md`,
2 file template, và bài tổng quan của hệ **chỉ khi cần** (`grep`).

**Không** đọc toàn bộ `README.md`, **không** đọc `BACKLOG-archive.md`.

## 3. Chọn việc

- Lấy **1–2** mục `chờ viết` ưu tiên cao nhất (trên → dưới; ưu tiên: tần suất
  lâm sàng > nguy cơ bỏ sót chết người > giá trị thi cử).
- Nếu có mục backfill-ảnh: dành 1 slot tìm ảnh cho bài thiếu.
- Mỗi lượt tối đa 2 bài — không nhồi thêm vì "còn thời gian".

## 4. Chống trùng (trước khi viết VÀ trước khi append)

```sh
python3 tools/check_duplicates.py <ID> "<tên bài>"
```

Exit **1** = ID/chủ đề đã tồn tại → **nâng cấp bài cũ** hoặc đổi chủ đề; không tạo bài mới.
ID trong BACKLOG có thể lệch thực tế: luôn kiểm bằng script, không tin số trong bảng.

## 5. Viết bài

Theo `medical-lesson-library` + `AGENTS.md`: thư mục `NNN-slug/` gồm
`lesson.md` + `sources.md` + `images/CREDITS.md`; Việt hóa 100%; nhãn certainty;
ma trận có **Chốt vào/Chốt loại**; Mermaid khi có RADS; Blind Quiz `<details>`;
mục (1) giải thích **TẠI SAO** bằng vật lý + mô bệnh, có số liệu định lượng.
Soi từng mục với `templates/gold-standard-lesson.md` trước khi xuất.

## 6. Ảnh

Thứ tự nguồn và luật license: theo bảng nguồn trong `AGENTS.md` và mục 4 của
`medical-lesson-library`. Tóm tắt quyết định:

- Europe PMC `FIG:"..." AND OPEN_ACCESS:Y` / Wikimedia → tải, ghi license **từng file**.
- Radiopaedia → chỉ từng ca, không crawl; AuntMinnie → chỉ dẫn link.
- Không có ảnh hợp phép → tự vẽ sơ đồ CC0, hoặc dẫn link (không bịa nguồn).
- CC BY-NC-ND: **nguyên bản**, không crop/ghép. Ảnh ghép dùng `tools/make_composite.py`.
- Tên file `NNN_slug_Modality_SourceID.jpg`; mỗi dòng CREDITS phải có license cụ thể.

## 7. Cập nhật hệ sinh thái

- Bài tổng quan của hệ: thêm hàng DDx / link bài mới (nếu có).
- `README.md`: thêm dòng ID (kiểm không lặp ID).
- `index.html`: thêm card + thumbnail (hoặc chạy `tools/build_index.py` nếu định dạng đã ổn).
- `BACKLOG.md`: flip mục vừa viết sang `xong` (kèm số liệu chính, ngắn).

## 8. Verify (không được bỏ)

Chạy theo skill `rad-verify`:

```sh
python3 tools/verify_all.py
```

- Exit 0 + 4/4 cổng + `index_parity_delta == 0` → được commit.
- FAIL → sửa và chạy lại; nếu không sửa được trong lượt → **không commit**,
  release khóa, báo lỗi cụ thể.

## 9. Commit + push

```sh
git add <đúng file của lượt>
git commit -m "feat(<ID>,<ID>): <chủ đề ngắn>"
git push origin master
```

Không `--force`, không `--no-verify`, không commit file ngoài phạm vi lượt.

## 10. Sau commit

- Append **tối đa 2** khoảng trống mới, chèn vào **đúng bảng** `## Hàng chờ viết`
  (không nối cuối file), mỗi mục đã qua `check_duplicates`.
- Nhật ký **≤ 2 dòng** vào `BACKLOG-archive.md`.
- `python3 tools/split_backlog.py --auto` (chỉ tách khi > 120 KB).
- Nếu đã append sau commit: `git add BACKLOG.md BACKLOG-archive.md && git commit --amend --no-edit`
  **chỉ khi** chưa push; nếu đã push thì commit riêng `chore(backlog): ...`.

## 11. Release khóa

`python3 tools/worker_guard.py release` — kể cả khi bước 8/9 FAIL.

## Xử lý sự cố

| Tình huống | Quyết định |
|---|---|
| BUSY (exit 3) | Dừng, không làm gì, báo 1 dòng |
| Pull conflict | Dừng, release, báo file conflict |
| Cây bẩn do lượt trước | Stash giữ việc (`-u`), ghi nhật ký, tiếp tục |
| Không tìm được ảnh hợp phép | Dẫn link hoặc vẽ sơ đồ CC0; không dùng ảnh license mơ hồ |
| Author-check FAIL | Sửa tên theo PMCID hoặc bỏ tên; không xóa PMCID để né |
| Verify FAIL không sửa kịp | Không commit, release, báo rõ cổng nào |
| Hết mục `chờ viết` | Báo hoàn tất, không bịa chủ đề mới |

## Đo lệch giữa các lượt

Sau verify, đọc dòng cuối `tools/verify_log.jsonl`:

- `lessons_total` tăng **+1/+2** so lượt trước (đúng số bài đã viết).
- `index_parity_delta == 0`, `lessons_missing_card == 0`.
- `backlog_waiting` không tăng quá +2 so với số đã viết (flip + append cân nhau).

Lệch bất thường 2 lượt liên tiếp → ghi 1 dòng cảnh báo trong báo cáo cuối, không tự sửa
luật. Không cần đọc cả file log.

## Mẫu trả lời cuối lượt (≤ 6 dòng)

```
bài: 197 (Li-Fraumeni) + 929 (xơ hóa nang) — 2 ảnh/1 composite, CC BY 4.0
verify: PASS 4/4 · 503 bài / 503 card · parity 0
backlog: flip #341/#340 → xong; append 2 mục (đã check_duplicates)
còn lại: 110 mục chờ viết; ưu tiên kế tiếp #342 ...
```

## Nguồn gốc (prompt cron cũ → nơi ở mới)

| Prompt cũ | Nay ở |
|---|---|
| Bước 0 khóa + release | mục 0, 11 |
| Bước 1 pull/stash/conflict | mục 1 |
| Bước 2 đọc file, giới hạn context | mục 2 |
| Bước 3 check_duplicates + khung 6 mục | mục 4–5 + `medical-lesson-library` |
| Bước 4 nguồn ảnh/license | mục 6 + `AGENTS.md` |
| Bước 5 cập nhật overview/README/index/BACKLOG | mục 7 |
| Bước 6 selfcheck/lint/mermaid/author | mục 8 + skill `rad-verify` |
| Bước 7 flip/append/archive/split | mục 10 |
| "QUY TẮC CỨNG" tên tác giả | `AGENTS.md` + mục 6 |
