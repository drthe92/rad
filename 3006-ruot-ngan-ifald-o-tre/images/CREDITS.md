# CREDITS — ảnh bài 3006 (Hội chứng ruột ngắn & IFALD ở trẻ)

Mỗi ảnh ghi rõ: file trong repo, hình gốc, bài gốc (PMCID), giấy phép, thay đổi phái sinh (nếu có).

| File | Hình gốc | Bài gốc | Giấy phép | Phái sinh |
|---|---|---|---|---|
| `3006_ruot-ngan_so-do_PMC10221592-F1.jpg` | Figure 1 — “Complications of short-bowel syndrome in children.” | Nutrients 2023, PMCID **PMC10221592** — https://europepmc.org/article/PMC/PMC10221592 | **CC BY 4.0** | Nguyên bản (giữ nguyên sơ đồ và nhãn tiếng Anh) |
| `3006_ifald_so-do_PMC10221592-F3.jpg` | Figure 3 — “Main reasons for occurrence of intestinal failure-associated liver disease (IFALD) in children with short-bowel syndrome.” | Nutrients 2023, PMCID **PMC10221592** — https://europepmc.org/article/PMC/PMC10221592 | **CC BY 4.0** | Nguyên bản (dùng để tham chiếu, không nhúng trực tiếp vào bài) |
| `3006_ifald_yeu-to_PMC12031023-F3.jpg` | Fig. 3 — “Factors contributing to the pathogenesis of IFALD. Factors contributing to the pathogenesis of IFALD include patient-related, infectious, surgical, and parenteral nutrient factors.” | Semin Liver Dis 2025, PMCID **PMC12031023** — https://europepmc.org/article/PMC/PMC12031023 | **CC BY 4.0** | Nguyên bản; **ghép cạnh** Fig. 4 vào `composite_ifald_yeu-to-co-che.jpg` (letterbox, không crop, không kéo giãn) |
| `3006_ifald_co-che_PMC12031023-F4.jpg` | Fig. 4 — “Proposed model of IFALD pathogenesis. (1) Intestinal dysfunction increases mucosal permeability … (2) … (3) … (4) …” | Semin Liver Dis 2025, PMCID **PMC12031023** — https://europepmc.org/article/PMC/PMC12031023 | **CC BY 4.0** | Nguyên bản; **ghép cạnh** Fig. 3 vào `composite_ifald_yeu-to-co-che.jpg` (letterbox, không crop) |
| `composite_ifald_yeu-to-co-che.jpg` | Ghép `3006_ifald_yeu-to_PMC12031023-F3.jpg` + `3006_ifald_co-che_PMC12031023-F4.jpg` | Semin Liver Dis 2025, PMCID **PMC12031023** | **CC BY 4.0** (cả hai ảnh nguồn) | Ảnh phái sinh: letterbox nền đen + dải nhãn `[Yếu tố nguy cơ IFALD]` / `[Cơ chế 4 bước]` + attribution; **không crop, không kéo giãn** (tạo bằng `tools/make_composite.py`) |
| `3006_ifald_sieu-am-tui-mat_PMC13696064-F1.jpg` | Figure 1 — “Abdominal ultrasonography at 5.0 months of age demonstrating persistence of cholelithiasis. (A) The gallbladder (GB) measured 2.30 cm in length and 1.17 cm in transverse diameter, with a wall thickness of 0.13 cm. (B) A single echogenic calculus of approximately 6.5 mm within the GB lumen (yellow arrow).” | Cureus 2026, PMCID **PMC13696064** — https://europepmc.org/article/PMC/PMC13696064 | **CC BY 4.0** | Nguyên bản (giữ nguyên panel A–B, nhãn “VESICULA BILAR”, “LITO” và thước đo của máy siêu âm) |

## Ghi chú
- **Tất cả ảnh dùng trong bài đều là CC BY 4.0** — được phép tái sử dụng, phái sinh và cả thương mại, miễn ghi công; repo là học liệu phi thương mại và ghi công đầy đủ.
- **Ảnh composite** chỉ ghép hai sơ đồ **cùng một bài gốc** (Semin Liver Dis 2025) — không ghép hai bệnh nhân/bài khác nhau để tránh gợi ý sai.
- **Tên tác giả KHÔNG ghi**: attribution dùng **tạp chí + năm + PMCID** (đối chiếu Europe PMC ngày 2026-10-28).
- Ảnh tải từ bản công khai của PMC (`cdn.ncbi.nlm.nih.gov/pmc/blobs/...`), đúng file của figure trong bài gốc; file `.webp` của Cureus được **chuyển sang JPEG không đổi nội dung**.
- Sơ đồ giữ **nhãn tiếng Anh nguyên bản** để không làm sai lệch hình gốc; phần giải thích tiếng Việt nằm trong `lesson.md`.
