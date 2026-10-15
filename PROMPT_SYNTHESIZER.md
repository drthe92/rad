# PROMPT_SYNTHESIZER.md — Chuẩn học thuật cho người/AI tổng hợp bài CĐHA

> Mọi bài `lesson.md` phải qua 4 cửa này trước khi commit. Nhãn mức chắc chắn + Việt hóa 100% theo `AGENTS.md`.

## 1. Ngưỡng định lượng bắt buộc (quantitative cut-offs)
- Không viết chung chung ("HU âm", "tăng tỷ trọng", "nốt nhỏ"). Mọi nhận định phải kèm số: khoảng HU, mm, ngày, phiên bản guideline.
- Ví dụ tối thiểu hệ Ngực: mỡ trong hamartoma **−40 đến −120 HU**; máu màng phổi **35–70 HU**; nhân đặc trong nốt bán đặc **≥ 6 mm** là ngưỡng hành động; thời gian nhân đôi thể tích (VDT) ác tính điển hình **20–400 ngày** (nốt bán đặc lepidic có thể chậm hơn nhiều).
- Ghi rõ phiên bản (Fleischner 2017, Lung-RADS v2022...) + ngưỡng xử trí tương ứng. Số nào chưa kiểm chứng được thì ghi "chưa rõ — cần tra", không bịa.

## 2. Nguyên lý cốt lõi theo hệ cơ quan (mở rộng từ học thuyết thể tích)
- **Hệ Ngực (001–099): Học thuyết thể tích (volume-loss doctrine)** — mất thể tích là chốt duy nhất Đông đặc vs Xẹp (phế quản hơi không loại trừ xẹp nói chung, chỉ mất khi tắc trung tâm hoàn toàn) + Golden S sign. Bổ sung khi sang bài mô kẽ: **tiểu thùy thứ cấp (secondary pulmonary lobule)** — trung tâm tiểu thùy vs bạch mạch vs ngẫu nhiên.
- **Hệ Bụng – Gan mật (100–199, chuẩn bị): Học thuyết động học bắt thuốc (enhancement kinetics)** — gan cấp máu kép (75% tĩnh mạch cửa, 25% động mạch gan) → u ác/HCC bắt thuốc mạnh thì động mạch (arterial hyperenhancement) + thải thuốc (washout) thì cửa/muộn.
- **Hệ Thần kinh (200–299, chuẩn bị): Hàng rào máu não (BBB) & khuếch tán (DWI/ADC)** + tiến triển hemoglobin theo thời gian trên T1/T2 (tối cấp → cấp → bán cấp sớm/muộn → mạn).

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
