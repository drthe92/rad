# CREDITS — ảnh bài 3057 (Vỡ khí quản – phế quản lớn sau đặt nội khí quản)

Mỗi ảnh ghi rõ: file trong repo, hình gốc, bài gốc (PMCID), giấy phép, thay đổi phái sinh (nếu có).

| File | Hình gốc | Bài gốc | Giấy phép | Phái sinh |
|---|---|---|---|---|
| `3057_vophkq_CT-axial_PMC13570639-F3.jpg` | Figure 3 — “Contrast-enhanced thoracic computed tomography, axial section at the level of the thoracic inlet. Subcutaneous emphysema of the anterior chest wall (arrow 1), diffuse pneumomediastinum (arrow 2), and disruption of the posterior membranous tracheal wall (arrow 3).” | Cureus 2026;18, PMCID **PMC13570639** — https://europepmc.org/article/PMC/PMC13570639 | **CC BY 4.0** | Nguyên bản (giữ nguyên khung, mũi tên và số 1–3) |
| `3057_vophkq_CT-sagittal_PMC13570639-F4.jpg` | Figure 4 — “Contrast-enhanced thoracic computed tomography, sagittal reformat. Diffuse pneumomediastinum (arrow 1), discontinuity of the posterior membranous tracheal wall (arrow 2) and subcutaneous emphysema of the anterior cervicothoracic soft tissues (arrow 3). The discontinuity corresponds to the lesion identified at bronchoscopy; the full extent found at thoracotomy was not appreciable on this imaging.” | Cureus 2026;18, PMCID **PMC13570639** — https://europepmc.org/article/PMC/PMC13570639 | **CC BY 4.0** | Nguyên bản (giữ nguyên mũi tên và số 1–3) |
| `composite_3057_CT-ngang-doc.jpg` | Ghép **Hình 3 + Hình 4** của cùng bài, cùng một bệnh nhân (CT ngang + dựng ảnh dọc) | Cureus 2026;18, PMCID **PMC13570639** | **CC BY 4.0** | **Ảnh ghép letterbox nền đen** bằng `tools/make_composite.py` — **không crop, không kéo giãn**, giữ nguyên tỷ lệ và toàn bộ mũi tên; dải đen ghi “A. CT ngang — mất liên tục thành sau / B. CT dọc — khí trung thất lan tỏa” |
| `3057_vophkq_noi-soi-te_PMC12752804-F2.jpg` | Figure 2 — “Bronchoscopic visualization of the posterior membranous tracheal tear. Flexible bronchoscopy revealing a longitudinal posterior membranous tracheal tear (red arrow) located approximately 1–2 cm above the carina (blue arrow). The defect appears without active bleeding, consistent with a partial-thickness tear. This finding confirmed the airway source of the patient's subcutaneous emphysema and pneumomediastinum.” | Cureus 2025;17, PMCID **PMC12752804** — https://europepmc.org/article/PMC/PMC12752804 | **CC BY 4.0** | Nguyên bản (giữ nguyên mũi tên đỏ và xanh) |
| `3057_vophkq_phan-do-cardillo_PMC9727090-F1.jpg` | Figure 1 — “Photograph depictions of PITL level I, level II, level IIIA and level IIIB.” (bốn ô nội soi có nhãn level I / II / IIIA / IIIB) | Front Surg 2022;9, PMCID **PMC9727090** — https://europepmc.org/article/PMC/PMC9727090 | **CC BY 4.0** | Nguyên bản (giữ nguyên bố cục 4 ô và nhãn) |

## Ghi chú
- **Cả bốn bài gốc của ảnh đều là CC BY 4.0** — được phép dùng, ghi công, tạo phái sinh; repo là học liệu phi thương mại, ghi công đầy đủ.
- **Ảnh ghép chỉ ghép 2 hình của CÙNG một bài, CÙNG một bệnh nhân** (PMC13570639, Hình 3 + Hình 4) — không ghép hai bệnh nhân khác nhau, không gợi ý sai về nguồn.
- **Không crop, không kéo giãn, không xóa mũi tên/nhãn** của tác giả; chỉ chuyển định dạng WebP → JPEG **không đổi pixel** (giữ nguyên độ phân giải gốc).
- **Tên tác giả KHÔNG ghi**: attribution dùng **tạp chí + năm + PMCID** (đối chiếu Europe PMC ngày 2026-11-05).
- Ảnh tải từ gói `supplementaryFiles` của Europe PMC (`https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/supplementaryFiles`), đúng file figure trong XML full-text của bài gốc.
- **Lưu ý nội dung ảnh:** Hình 2 của PMC12752804 được tác giả mô tả là **rách bán phần** trên nội soi; bài dùng ảnh này để minh họa **vị trí và cơ chế** (sau thay ống), không dùng để suy ra toàn thành.
