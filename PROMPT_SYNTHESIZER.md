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
- **Hệ Cơ – Xương – Khớp (300–399): Học thuyết tốc độ phát triển (Lodwick & Zone of transition) + Vật lý tủy xương T1W** — mọi tiêu xương đánh giá bằng vùng chuyển tiếp (hẹp = chậm/lành IA-IB, rộng = nhanh/ác II-III; ngoại lệ > 40 tuổi: myeloma/di căn). Tủy vàng trưởng thành (80% mỡ) T1W luôn sáng hơn cơ/đĩa đệm: **thay thế tủy thật (T1W tối hơn cơ/đĩa + SII ≤ 20%)** vs phù/tủy đỏ (T1W ≥ cơ + SII > 20%).
- **Hệ Vú & Sản Phụ khoa (500–599): Động học DCE (Type I/II/III) + Giải phẫu 3 lớp tử cung + Vật lý khối phần phụ** — u ác ngấm nhanh-thoát sớm (**Type III washout giảm > 10%** / Type II plateau), lành ngấm chậm tăng dần (Type I persistent). Tử cung T2W 3 lớp: nội mạc sáng + **vùng chuyển tiếp JZ tối (thường ≤ 8 mm; ≥ 12 mm = adenomyosis)** + cơ ngoài trung gian. Khối T1 sáng: **mất tín hiệu T1 fat-sat = mỡ (dermoid)** vs vẫn sáng = máu/nhầy (endometrioma); **T2 shading** = máu cũ nhiều đợt; **đặc tối đen T2 + tối DWI = xơ lành (fibroma, O-RADS 2)**.

## 3. Trung thành nguồn + phản biện (fidelity + critique)
- Ca nguyên văn: giữ đúng mô bệnh/chú thích gốc (kể cả khi không điển hình), ghi rõ Fig/ID nguồn.
- Nếu ca không điển hình (vd nốt gai ngoại vi 15 mm mà mô bệnh là SCLC — trong khi SCLC ~90% trung tâm), **thêm chú thích phản biện** ngay dưới đáp án, không sửa nguồn.
- Kiểm chứng lại mọi ca trước khi đưa vào quiz: đối chiếu bài gốc (vd PMC/DOI), không tin mù chú thích trung gian.

## 4. Cạm bẫy mặt cắt (cross-sectional pitfalls)
- Mọi bài màng phổi/bụng phải có mục phân biệt trên CT ngang: **dịch màng phổi vs cổ trướng (ascites)** — dấu crus lệch (displaced crus sign), dấu bare area (bare area sign), meniscus vs ôm gan/lách.
- Nguyên tắc chung: cùng một đậm độ dịch, vị trí tương đối với cơ hoành/crus mới quyết định tên gọi.

## Quy trình áp cho từng bài
1. Gom nguồn vào `sources.md` → kiểm phép từng ảnh → tải về đặt tên `NNN_slug_Modality_SourceID`.
2. Đọc sâu full-text + bảng guideline (Fleischner/ACR toàn văn, Fig/Table có số) — không viết từ abstract. Đối chiếu từng mục với `templates/gold-standard-lesson.md` (bài 025 mẫu vàng).
3. Viết `lesson.md` đúng khung 6 mục + frontmatter, số liệu định lượng ở mục (1)/(4), ma trận đối chiếu có 2 cột Chốt vào/Chốt loại.
4. Quiz `<details>`: ảnh trơn ngoài, findings + chẩn đoán + nguồn trong; ca không điển hình thêm dòng phản biện.
5. Chạy `python3 tools/selfcheck.py` — PASS mới được commit (không force-push). FAIL thì sửa hết lỗi rồi chạy lại.

## Phụ lục Mắt & thị giác (400–499) — áp nghiêm ngặt mọi bài dải 400
1. **Giải phẫu cơ vận nhãn:** thân cơ to **chừa gân (tendon-sparing)** = Graves (TED); **cả gân (involving tendons)** = giả u viêm/myositis/cellulitis. Mọi tổn thương hốc mắt phải định vị **trong nón (intraconal) vs ngoài nón (extraconal)**.
2. **Protocol:** CT lát mỏng **≤ 1 mm** + cản quang (mạch/thành/vỡ xương); MRI hốc mắt bắt buộc **T1 fat-sat sau tiêm + T2 fat-sat** (viêm/u thần kinh thị/cơ mắt).
3. **Ma trận vôi hóa nhãn cầu nhi:** Retinoblastoma (**vôi hóa thô to**, < 5 tuổi, RB1) vs Coats (**xuất huyết, KHÔNG vôi hóa điển hình**) vs PHPV (dây xơ thể thủy tinh).
4. **Tuân thủ:** đúng 6 mục; định lượng bằng số (**mm, mmHg, HU, % RNFL**); ma trận 2 cột Chốt vào/Chốt loại; quiz `<details>` như hệ Ngực.
