# Rad metrics — đọc khi chỉ số bất thường

`verify_all.py` ghi các chỉ số này vào `tools/verify_report.json` và
`tools/verify_log.jsonl`. Chỉ số không tự chặn trừ khi đã thành cổng.

| Chỉ số | Kỳ vọng | Khi bất thường |
|---|---|---|
| `index_parity_delta` | 0 | Thiếu/thừa card so với folder; sửa card, không sửa folder cho khớp |
| `lessons_missing_card` | 0 | Bài chưa có card; thêm card + thumbnail |
| `images_referenced_uncredited` | 0 | Ảnh đang hiển thị thiếu dòng CREDITS; thêm license + link gốc |
| `images_unreferenced_uncredited` | 0 | Ảnh mồ côi không credit; credit đúng hoặc xóa file |
| `images_unreferenced` | không phải lỗi | Nguồn composite/bản cũ; chỉ điều tra nếu tăng bất thường |
| `backlog_duplicate_ids` | 0 | ID trùng trong BACKLOG; gộp hoặc đổi ID |
| `selfcheck_warnings` | 15 legacy | Tăng: có bài mới thiếu ma trận 2 cột; giảm: cập nhật baseline |
| `backlog_waiting` | không tăng quá +2/lượt | Flip và append không cân; kiểm lại bước 10 |

Quy tắc: chỉ số xấu **hai lượt liên tiếp** thì báo người dùng ở dòng cuối; không
tự nới luật, không tự chặn pipeline.

Chi tiết định nghĩa nằm trong `tools/verify_all.py` và `tools/verify_report.json`.
