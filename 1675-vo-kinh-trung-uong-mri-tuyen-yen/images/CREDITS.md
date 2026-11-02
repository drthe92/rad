# CREDITS — ảnh bài 1675 (Vô kinh trung ương trên MRI tuyến yên)

Mỗi ảnh ghi rõ: file trong repo, hình gốc, bài gốc (PMCID), giấy phép, phái sinh (nếu có).

| File | Hình gốc | Bài gốc | Giấy phép | Phái sinh |
|---|---|---|---|---|
| `1675_vo-kinh-trung-uong_MRI-T1gd_PMC12839661-f1.jpg` | Figure 1 — "Sagittal T1-weighted image after Gadolinium injection showing a heterogeneous enhancement of the pituitary mass consistent with a NFPMA" | *Diagnostics (Basel)* 2026, PMCID **PMC12839661** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12839661/ | **CC BY 4.0** | Nguyên bản; **có** dùng trong ảnh ghép `composite_macroadenoma-vs-viem-tuyen-yen.jpg` |
| `1675_vo-kinh-trung-uong_MRI-T1gd_PMC12839661-f2.jpg` | Figure 2 — "Sagittal T1-weighted image after Gadolinium injection showing a homogeneous enhancement of the pituitary mass in the case of hypophysitis" | *Diagnostics (Basel)* 2026, PMCID **PMC12839661** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12839661/ | **CC BY 4.0** | Nguyên bản; **có** dùng trong ảnh ghép `composite_macroadenoma-vs-viem-tuyen-yen.jpg` |
| `1675_vo-kinh-trung-uong_MRI-T1gd_PMC12839661-f3.jpg` | Figure 3 — "Coronal T1-weighted image after Gadolinium administration showing a NFPMA displacing the normal residual pituitary tissue leftward, which enhances homogeneously and intensely" | *Diagnostics (Basel)* 2026, PMCID **PMC12839661** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12839661/ | **CC BY 4.0** | Nguyên bản (không crop) |
| `1675_vo-kinh-trung-uong_MRI-T2_PMC12839661-f4.jpg` | Figure 4 — "Coronal T2-weighted image showing a peripheral hypointense rim surrounding the parasellar region (white arrows) in a patient with a sellar mass extending superiorly into the suprasellar cistern, consistent with hypophysitis" | *Diagnostics (Basel)* 2026, PMCID **PMC12839661** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12839661/ | **CC BY 4.0** | Nguyên bản; **không** dùng trong ảnh ghép (khác chuỗi xung) |
| `1675_vo-kinh-trung-uong_MRI-T1_PMC12246542-f1.jpg` | Figure 1 — "Sagittal MR image of the pituitary. A, T1WI on day 6 … anterior lobe is swollen with a diffuse low signal … normal high signal of the posterior lobe. B, T2WI on day 6 … C, T1WI on day 12 … high signal of the posterior lobe is absent. D, Contrast enhancement on day 12 … E, T1WI on day 45, anterior lobe is atrophic … F, Contrast enhancement on day 45" (6 panel A–F) | *JCEM Case Rep* 2025, PMCID **PMC12246542** — https://pmc.ncbi.nlm.nih.gov/articles/PMC12246542/ | **CC BY 4.0** | Nguyên bản (6 panel gốc) |
| `composite_macroadenoma-vs-viem-tuyen-yen.jpg` | Ghép **side-by-side** từ 2 ảnh trên (Fig 1 + Fig 2, cùng **T1 sau tiêm, sagittal**), dải đen ghi nhãn `Macroadenoma - T1gd sagittal \| PMC12839661, CC BY` và `Viêm tuyến yên - T1gd sagittal \| PMC12839661, CC BY` | *Diagnostics (Basel)* 2026, PMCID **PMC12839661** | **CC BY 4.0** | **Phái sinh**: letterbox nền đen, **không crop, không kéo giãn** (giữ aspect gốc); tạo bằng `tools/make_composite.py` |

## Ghi chú
- **Tất cả ảnh nguồn là CC BY 4.0** → được phép tái bản và **tạo phái sinh** với điều kiện ghi nguồn + giấy phép; repo ghi attribution ngay trong dải đen của ảnh ghép.
- Ảnh T2 (Fig 4) **không** đưa vào ảnh ghép vì **khác chuỗi xung** — ghép T2 với T1 sẽ làm sai so sánh.
- **Không crop, không kéo giãn, không đổi nội dung** bất kỳ ảnh nào; nhãn/mũi tên của hình gốc giữ nguyên.
- **Tên tác giả KHÔNG ghi**: attribution dùng **tạp chí + năm + PMCID** (đối chiếu Europe PMC ngày 2026-11-02).
- Ảnh lấy từ **gói toàn văn mở Europe PMC** (`/supplementaryFiles`) của đúng PMCID.
