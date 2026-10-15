# PROMPT_SYNTHESIZER.md — Chuẩn học thuật cho người/AI tổng hợp bài CĐHA

> Mọi bài `lesson.md` phải qua 4 cửa này trước khi commit. Nhãn mức chắc chắn + Việt hóa 100% theo `AGENTS.md`.

## 1. Ngưỡng định lượng bắt buộc (quantitative cut-offs)
- Không viết chung chung ("HU âm", "tăng tỷ trọng", "nốt nhỏ"). Mọi nhận định phải kèm số: khoảng HU, mm, ngày, phiên bản guideline.
- Ví dụ tối thiểu hệ Ngực: mỡ trong hamartoma **−40 đến −120 HU**; máu màng phổi **35–70 HU**; nhân đặc trong nốt bán đặc **≥ 6 mm** là ngưỡng hành động; thời gian nhân đôi thể tích (VDT) ác tính điển hình **20–400 ngày** (nốt bán đặc lepidic có thể chậm hơn nhiều).
- Ghi rõ phiên bản (Fleischner 2017, Lung-RADS v2022...) + ngưỡng xử trí tương ứng. Số nào chưa kiểm chứng được thì ghi "chưa rõ — cần tra", không bịa.

## 2. Học thuyết thể tích (volume-loss doctrine) — Đông đặc vs Xẹp
- **Mất thể tích (volume loss) là CHỐT DUY NHẤT** phân biệt xẹp phổi với đông đặc, không phải phế quản hơi.
- **Phế quản hơi (air bronchogram) KHÔNG loại trừ xẹp nói chung**: xẹp thụ động (tràn dịch ép) và xẹp co kéo vẫn có phế quản hơi, thậm chí tụ lại (crowded). Nó chỉ biến mất khi **tắc nghẽn trung tâm hoàn toàn** (khí không vào được).
- Mọi bảng DDx đông đặc/xẹp phải có cột dấu thể tích (rãnh liên thùy, trung thất, cơ hoành, khoảng liên sườn).
- Dấu kinh điển phải dạy kèm ảnh: **Golden S sign** — xẹp thùy trên phải + u trung tâm: bờ dưới lồi (u) + bờ trên lõm (rãnh bé kéo lên).

## 3. Trung thành nguồn + phản biện (fidelity + critique)
- Ca nguyên văn: giữ đúng mô bệnh/chú thích gốc (kể cả khi không điển hình), ghi rõ Fig/ID nguồn.
- Nếu ca không điển hình (vd nốt gai ngoại vi 15 mm mà mô bệnh là SCLC — trong khi SCLC ~90% trung tâm), **thêm chú thích phản biện** ngay dưới đáp án, không sửa nguồn.
- Kiểm chứng lại mọi ca trước khi đưa vào quiz: đối chiếu bài gốc (vd PMC/DOI), không tin mù chú thích trung gian.

## 4. Cạm bẫy mặt cắt (cross-sectional pitfalls)
- Mọi bài màng phổi/bụng phải có mục phân biệt trên CT ngang: **dịch màng phổi vs cổ trướng (ascites)** — dấu crus lệch (displaced crus sign), dấu bare area (bare area sign), meniscus vs ôm gan/lách.
- Nguyên tắc chung: cùng một đậm độ dịch, vị trí tương đối với cơ hoành/crus mới quyết định tên gọi.

## Quy trình áp cho từng bài
1. Gom nguồn vào `sources.md` → kiểm phép từng ảnh → tải về đặt tên `NNN_slug_Modality_SourceID`.
2. Viết `lesson.md` đúng khung 6 mục + frontmatter, số liệu định lượng ở mục (1)/(4), ma trận đối chiếu có 2 cột Chốt vào/Chốt loại.
3. Quiz `<details>`: ảnh trơn ngoài, findings + chẩn đoán + nguồn trong; ca không điển hình thêm dòng phản biện.
4. Tự kiểm: bảng cân cột, ảnh tồn tại, link chéo đúng ID 3 số → commit + push (không force-push).
