# AGENTS.md — Thư viện Chẩn đoán hình ảnh

> Repo học chẩn đoán hình ảnh (CĐHA) từ nguồn mở. Publish GitHub Pages tại `rad.matcauvong.com` (`index.html` làm hub tra cứu). Kế thừa phương pháp từ project Thư viện Phẫu thuật Mắt.

## Mục tiêu
1. Bác sĩ CĐHA nắm **bản chất vấn đề + chẩn đoán phân biệt (diagnosis, differential diagnosis)**, không học vẹt từng ca (case).
2. Học liệu lưu lâu dài trong repo, tra cứu trên web theo lộ trình.

## Nguồn (kiểm chứng giấy phép từng nguồn trước khi tải ảnh)
| Nguồn | Điểm mạnh | Giấy phép ảnh / quy tắc |
|---|---|---|
| Radiopaedia.org | Ca (case) theo hệ (system), giàu ảnh X-quang (radiograph)/CT/MRI | Đa số CC BY-NC-SA — tải về được, ghi nguồn, phi thương mại (non-commercial) |
| The Radiology Assistant (RNL) | Bài tổng quan (review) theo chủ đề, sơ đồ (diagram) đẹp | Giáo dục — dẫn link (link) chính, ảnh xin phép/tải khi cho phép |
| LearningRadiology.com | Nhận diện mẫu hình (pattern recognition), quiz | Dẫn link; ảnh theo điều khoản trang |
| Eurorad (ESR) | Ca có bình duyệt (peer-reviewed) | Giáo dục — ghi nguồn đầy đủ |
| MedPix (NCI) | Ca + câu hỏi | Miễn phí học tập |
| RSNA Case Collection | Ca chuẩn hội Điện quang Bắc Mỹ (Radiological Society of North America) | Tuân thủ điều khoản RSNA |
| AuntMinnie (Case of the Day) | Ca mỗi ngày | Nhiều phần paywall — **chỉ dẫn link, không tải** |
| Stanford Medicine 25 | Khám lâm sàng (physical exam) + hình ảnh | Dẫn link |
| Wikimedia Commons (Category:Radiology) | Ảnh mở | Kiểm tra giấy phép từng file (CC đủ loại) |
| Cybersight / EyeRounds | Mắt (siêu âm (ultrasound), CT/MRI hốc mắt (orbit)) | Miễn phí học tập |
| CataractCoach | Video (video) phẫu thuật (tham khảo can thiệp (intervention)) | Dẫn link |
| Europe PMC (europepmc.org) | Tìm ảnh trong caption (cú pháp `FIG:"dấu hiệu" AND OPEN_ACCESS:Y`), REST API miễn phí, kèm PMCID/DOI + giấy phép | CC BY/CC0 theo từng bài — ghi đúng license từng ảnh |
| PubMed Central (PMC, lọc open access) | Bản full-text + ảnh gốc độ phân giải cao; Insights into Imaging 100% CC BY 4.0 | CC BY 4.0 (Insights Imaging) / theo từng bài |
- Lưu ý: Open-i (NLM) đã ngừng hoạt động — KHÔNG dùng; thay bằng 2 cổng trên (đã kiểm chứng: tìm `FIG:"Golden S sign"` ra 5 bài OA; đối chiếu chú thích Snoeckx 2018 qua PMCID).

## Quy ước bất biến
- Mỗi chủ đề một folder `NNN-slug/` (NNN = ID (identifier) 3 chữ số, ổn định, KHÔNG BAO GIỜ đánh lại số).
- Mỗi bài: `images/` (tải về, ghi nguồn + giấy phép từng ảnh; không tải được thì dẫn link) + `lesson.md` (mở đầu bằng frontmatter YAML gọn, map từ schema Gamut-First của Argon) + `sources.md` (link gốc).
- Frontmatter bắt buộc: `unit_id, subspecialty, anatomical_location, primary_pattern, tags[pattern/vung/score/anatomy/protocol/incidentaloma], certainty`. (Link nguồn KHÔNG nằm trong frontmatter — ở `sources.md` + `images/CREDITS.md`; `index.html` hiện link tay, chưa parse tự động.)
- `lesson.md` đúng khung 6 mục (xem `templates/lesson-template.md`):
  1. Tổng quan bệnh học (pathology)-cơ chế hình ảnh (imaging mechanism);
  2. Mẫu hình (pattern) + chẩn đoán phân biệt theo vị trí (gamut, theo vị trí (location));
  3. Bảng so sánh phân biệt (ma trận đối chiếu — bắt buộc 2 cột Chốt vào/Chốt loại theo Argon);
  4. Protocol (giao thức) chụp + hệ phân độ/điểm chuẩn hóa (scoring/grading system) + sơ đồ Mermaid flowchart khi có RADS (Fleischner, Lung-RADS trước);
  5. Biến thể bình thường (normal variant) và cạm bẫy (pitfall);
  6. Tự lượng giá 3 câu.
- **Việt hóa 100%**: tiếng Việt lên trước, thuật ngữ Anh giữ trong ngoặc ở lần đầu (để tra y văn (literature)).
- Nhãn mức chắc chắn (certainty level) mỗi bài, ghi rõ ở đầu bài: `ca nguyên văn (verbatim case)` / `tổng hợp y văn (literature synthesis)` / `suy luận (inference)`.
- Quy tắc ảnh (image rule): tải về nếu giấy phép cho phép (ghi nguồn + giấy phép từng ảnh trong `images/CREDITS.md`), không tải được thì dẫn link. AuntMinnie: chỉ dẫn link. Tên file: `NNN_slug_Modality_SourceID.jpg` (vd `020_not-phoi_CT_Radiopaedia-rIDxxxxx.jpg`). Ảnh ghép đối chiếu: `images/composite_*.jpg` tạo bằng `tools/make_composite.py` (Pillow letterbox nền đen — KHÔNG crop/kéo giãn, giữ aspect gốc — + dải đen `[Tên bệnh - chuỗi xung] + attribution`), nhúng vào mục (3).
- Blind Quiz ngay trên trang tĩnh: mỗi ca đặt ảnh + câu hỏi gợi mở ở NGOÀI, giấu findings + chẩn đoán trong `<details><summary>` (xem template mục 6). Không cần app/Streamlit phase này.
- Không dùng để chẩn đoán độc lập khi chưa có người hướng dẫn (Disclaimer y tế, ghi ở `lesson.md` + `index.html` footer).
- Không bao giờ force-push.

## Hub tra cứu (index.html, 4 kiểu tra cứu của bác sĩ CĐHA)
1. **Mẫu hình + Vị trí (Pattern/Gamut)**: lọc theo tags `pattern:*` + `vung:*` (ví dụ: pattern:nốt + vùng:phổi).
2. **Phân độ & bảng điểm (Scoring)**: từ khóa `score:*` (BI-RADS (Breast Imaging Reporting and Data System), Lung-RADS (Lung Imaging Reporting and Data System), TI-RADS (Thyroid Imaging Reporting and Data System), LI-RADS (Liver Imaging Reporting and Data System), PI-RADS (Prostate Imaging Reporting and Data System), Fleischner, Bosniak...).
3. **Giải phẫu cắt lớp (cross-sectional anatomy) & biến thể bình thường**: tag `anatomy:*`, file tổng quan riêng từng vùng.
4. **Protocol & tổn thương tình cờ (incidentaloma)**: tag `protocol:*`, `incidentaloma:*` (Fleischner nốt phổi (pulmonary nodule), Bosniak nang thận (renal cyst)...).
- Mỗi thẻ (card): số ID + tên Việt/Anh + link Bài học + link nguồn (tab mới) + thumbnail local.
- Search khớp cả số ID, tên Việt/Anh, tag.

## Quy trình combo (mỗi chủ đề)
1. Quét TẤT CẢ nguồn trong bảng cho chủ đề → gom video/ca/bài vào `sources.md`.
2. Viết `lesson.md` đúng khung 6 mục, tải ảnh (ghi giấy phép vào `images/CREDITS.md`), không tải được thì dẫn link.
3. Viết/cập nhật Tổng quan chủ đề (bảng so sánh chẩn đoán phân biệt (differential diagnosis, DDx) là bắt buộc) + mục Bài liên quan chéo.
4. Cập nhật index (dòng index + thẻ hub + tags 4 chiều) → commit + push sau MỖI đợt (SSH có sẵn). Không bao giờ force-push.
5. Rà soát trùng lặp định kỳ mỗi khi xong một hệ cơ quan (organ system).

## Quy tắc số-nhóm
- Số folder là ID ổn định để giao tiếp; nhóm/tag để xếp học, đổi thoải mái.
- Chỉ tách tag con khi một nhóm quá đông (~15–20 bài).
- ID quá 1000: không vướng (parse số bằng int, tham chiếu bằng tên chính xác).
- Dải ID (3 chữ số, chừa khe chèn): Ngực `001–080` (xong); **Bụng `100–180`** (bản đồ trong `100-tong-quan-he-bung/lesson.md`, Đợt 1: 110/121/135/150/155/160); Thần kinh `200–299`; Cơ xương `300–399`; **Mắt & thị giác `400–460`** (xong)...
- Mục (1) bắt buộc giải thích TẠI SAO (vật lý T1/T2/DWI/HU + mô bệnh), không chỉ liệt kê tín hiệu — theo PROMPT_SYNTHESIZER của Argon + nhãn certainty của ta.
- Mọi bài qua 4 cửa trong `PROMPT_SYNTHESIZER.md` (ngưỡng định lượng, học thuyết thể tích, trung thành nguồn + phản biện, cạm bẫy mặt cắt) trước khi commit.
- Bài mới phải soi với `templates/gold-standard-lesson.md` (bài 025 mẫu vàng) + chạy `python3 tools/selfcheck.py` PASS mới commit.

## Phân công (ta vs Argon — ai giỏi việc gì làm việc đó)
- Ta (OpenChamber/Build): khung repo, ID, hub Pages, script composite, Mermaid, kiểm phép ảnh, commit/push.
- Argon (Gemini): tổng hợp nội dung học thuật từ nguồn đã tải hợp phép → xuất frontmatter + ma trận đối chiếu + giải thích vật lý + quiz mù. Không giao Argon scrape hàng loạt (vi phạm ToS) hay push trực tiếp.

## Cấu trúc repo
```
AGENTS.md
README.md
index.html          # hub tra cứu, publish Pages, CNAME rad.matcauvong.com
templates/
  lesson-template.md
  sources-template.md
tools/
  make_composite.py   # Pillow: ghép lưới + dải đen attribution (chạy local)
001-tong-quan-he-nguc/   # Tổng quan hệ Ngực (bảng DDx bắt buộc + Bài liên quan)
010-giai-phau-nguc-cat-lop/
020-not-phoi/
030-dong-dac-xep-phoi/
040-tran-dich-mang-phoi/
mỗi NNN-slug/: lesson.md (frontmatter YAML) + sources.md + images/CREDITS.md
```
