# CREDITS — ảnh bài 1667 (Tắc ruột non do dính ở thai phụ)

Mỗi ảnh ghi rõ: file trong repo, hình gốc, bài gốc (PMCID), giấy phép, phái sinh (nếu có).

| File | Hình gốc | Bài gốc | Giấy phép | Phái sinh |
|---|---|---|---|---|
| `1667_tac-ruot-dinh-thai-phu_MRI_PMC13373904-f1.jpg` | Figure 1 — "Transverse view of abdominal MRI suggestive of SBO. A: Afferent dilated bowel loop, B: Point of transition, C: Distal collapsed bowel loop, D: Right hydroureter, E: Dilated small bowel loop, F: Foetus, G: Placenta" | *Cureus* 2026, PMCID **PMC13373904** — https://pmc.ncbi.nlm.nih.gov/articles/PMC13373904/ | **CC BY 4.0** | Nguyên bản (giữ nhãn A–G) |
| `1667_tac-ruot-dinh-thai-phu_MRI_PMC13373904-f2.jpg` | Figure 2 — "Coronal view of abdominal MRI showing point of transition. The arrow points to the single point of transition that caused mechanical blockage of intestinal contents" | *Cureus* 2026, PMCID **PMC13373904** | **CC BY 4.0** | Nguyên bản |
| `composite_tac-ruot-dinh-thai-phu_MRI.jpg` | Ghép **Hình 1 + Hình 2** của cùng ca (axial + coronal) | *Cureus* 2026, PMCID **PMC13373904** | **CC BY 4.0** | **Ảnh ghép** do `tools/make_composite.py` tạo (letterbox nền đen, giữ nguyên aspect, dải chú thích ghi tên bệnh + attribution) |
| `1667_tac-ruot-dinh-thai-phu_MRI_PMC10528125-f3.jpg` | Figure 3 — "A 21-year-old, third-trimester pregnant woman with known inflammatory bowel disease, presenting with severe abdominal pain. Coronal (a) and axial HASTE (b) images show multiple dilated fluid-filled bowel loops upstream of the ileostomy in the right iliac fossa. At this level, laparoscopy confirmed the presence of adhesions." | *Diagnostics (Basel)* 2023, PMCID **PMC10528125** — https://pmc.ncbi.nlm.nih.gov/articles/PMC10528125/ | **CC BY 4.0** | Nguyên bản (2 panel a–b) |
| `1667_tac-ruot-dinh-thai-phu_SO-do_PMC12297560-f1.jpg` | Fig. 1 — "Flowchart for the management of adhesive small bowel obstruction during pregnancy" (50 thai phụ nghi ASBO → loại 7 → 22 bảo tồn thường / 21 bảo tồn + gastrografin 100 mL) | *Sci Rep* 2025, PMCID **PMC12297560** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12297560/ | **CC BY-NC-ND 4.0** | Nguyên bản (**NC-ND: không crop, không ghép**) |

## Ghi chú
- **Ảnh ghép duy nhất** (`composite_...`) ghép **hai hình của CÙNG một bệnh nhân, cùng chuỗi xung T2**, đúng quy ước `tools/make_composite.py`: letterbox nền đen, **không crop/kéo giãn**, dải đen ghi `[Tên bệnh – chuỗi xung] + attribution`.
- **PMC12297560 là CC BY-NC-ND 4.0** → chỉ dùng **nguyên bản**, không đưa vào ảnh ghép.
- **Tên tác giả KHÔNG ghi**: attribution dùng **tạp chí + năm + PMCID** (đối chiếu Europe PMC ngày 2026-11-01) để tránh gán sai tên.
- Ảnh tải từ **PMC** (`cdn.ncbi.nlm.nih.gov/pmc/blobs/...`), đúng file figure gốc; không chỉnh sửa nội dung.
