# Nguồn gốc — 1784-hoi-chung-tuoi-mau-qua-muc-sau-tai-thong-moyamoya (hội chứng tưới máu quá mức sau tái thông moyamoya)

> Quét ngày 2026-10-31: Europe PMC (`("cerebral hyperperfusion syndrome" AND moyamoya) AND OPEN_ACCESS:Y`) + truy vấn PMID của meta-analysis. Chỉ dùng bài open access có giấy phép rõ ràng; không lấy ảnh từ nguồn không rõ license.

| # | Nguồn | Tiêu đề / Ca | Link gốc | Giấy phép ảnh | Ảnh đã tải |
|---|---|---|---|---|---|
| 1 | Neurosurgical Review 2025 (PMID 41392131) | *Incidence of cerebral hyperperfusion syndrome following revascularization surgery in moyamoya patients: a systematic review and meta-analysis* | https://pubmed.ncbi.nlm.nih.gov/41392131/ | Không lấy ảnh (chỉ số liệu gộp) | — |
| 2 | Front Neurol 2025 (PMC12852945) | *Preoperative local hemodynamics predict cerebral hyperperfusion syndrome after direct bypass for moyamoya disease: a quantitative CTP study based on ASPECTS topography* | https://pmc.ncbi.nlm.nih.gov/articles/PMC12852945/ | **CC BY 4.0** | `1784_hoi-chung-tuoi-mau_DSA-CTP-ASL_PMC12852945.jpg` |
| 3 | Front Physiol 2026 (PMC13461402) | *Postoperative perfusion volume on territorial arterial spin labeling provides an exploratory risk signal for cerebrovascular autoregulation failure after moyamoya revascularization* | https://pmc.ncbi.nlm.nih.gov/articles/PMC13461402/ | **CC BY 4.0** | `1784_hoi-chung-tuoi-mau_ASL_PMC13461402.jpg` |
| 4 | Front Neurol 2026 (PMC13527932) | *Intraoperative transit-time flowmetry of the superficial temporal artery directly predicts and may mitigate risk of postoperative hyperperfusion syndrome in moyamoya bypass surgery* | https://pmc.ncbi.nlm.nih.gov/articles/PMC13527932/ | **CC BY 4.0** | (số liệu STA-Cut; không lấy ảnh) |
| 5 | Front Neurol 2026 (PMC13677357) | *Perioperative ASL-derived CBF changes are associated with complications after Moyamoya bypass surgery* | https://pmc.ncbi.nlm.nih.gov/articles/PMC13677357/ | **CC BY 4.0** | `1784_hoi-chung-tuoi-mau_CT-xuat-huyet_PMC13677357.jpg`; `1784_hoi-chung-tuoi-mau_CT-MRI-nhoi-mau_PMC13677357.jpg` |
| 6 | Front Neurol 2025 (PMC12511514) | *Moyamoya disease: epidemiology, clinical features, pathogenesis, diagnosis and therapeutic interventions* (bối cảnh CHS 21,5–50%) | https://pmc.ncbi.nlm.nih.gov/articles/PMC12511514/ | CC BY 4.0 | (bối cảnh; không lấy ảnh) |

## Số liệu chính đã dùng (đối chiếu đúng bài gốc)

- **Meta-analysis (PMID 41392131):** 23 nghiên cứu/**2.083 ca**; CHS gộp **23% (95% CI 17–30%)**; **trực tiếp 27%**, **phối hợp 21%**; động kinh sau mổ **8% (5–11%)**; xuất huyết **15% (7–24%)**.
- **PMC12852945:** 103 bán cầu/12 CHS (**11,65%**); thời điểm **15 phút – 6 ngày**; triệu chứng thường trong **2 ngày**, tự khỏi trong **2 tuần**; **Suzuki OR 8,87 (1,44–54,45)**; **PCA Tmax OR 0,03 (0,00–0,69)**; mô hình **AUC 0,83**, cut-off **0,060**; protocol hạ áp **120–130 mmHg**, dịch **30–50 mL/kg**, chống động kinh **100 mg/ngày**.
- **PMC13461402:** 116 ca/13 CHS (**11,2%**); tiêu chuẩn hình ảnh **CBF tăng > 100%** so với trước mổ; **THA OR 17,565 (4,371–70,584)**; **Suzuki IV OR 8,213 (1,460–46,193)**; tuổi **≥ 61** (Se 69,2%/Sp 95,1%); thể tích tASL **> 104,45 cm³** (Se 69,2%/Sp 67,0%); đường trên rãnh Sylvius **16,7% vs 5,4%** (p = 0,077).
- **PMC13527932:** **12,74%** CHS; **STA-Cut ≤ 40,5 mL/phút** (AUC 0,843; Se 66,3%; Sp 100%); CHS **26,15 ± 9,54** vs không CHS **63,88 ± 38,01** mL/phút (p = 0,0006); MBC ≤ 4: **11/13 vs 41/89** (p = 0,015).
- **PMC13677357:** 146 ca; xuất huyết **8 (5,5%)**, nhồi máu **14 (9,6%)**, động kinh **9 (6,2%)**; **ΔCBF > 43,48** → xuất huyết (AUC 0,989; Se 100%; Sp 95,65%; PPV 57,1%; NPV 100%); **ΔCBF ≤ 4,48** → nhồi máu (AUC 0,915; Se 92,86%; Sp 78,79%; PPV 31,7%; NPV 99,0%); 8/14 (57,1%) xuất huyết khi trên ngưỡng vs 0/132 dưới ngưỡng (p = 7,13 × 10⁻¹⁰); 13/41 (31,7%) nhồi máu khi dưới ngưỡng vs 1/105 (1,0%) trên ngưỡng (p = 1,56 × 10⁻⁷).

## Ghi chú giấy phép

- Ba bài lấy ảnh đều **CC BY 4.0** (đọc trực tiếp từ trường `license` trong XML full-text của Europe PMC) — được phép tái sử dụng, kể cả tạo ảnh phái sinh, miễn ghi công.
- Ảnh được tải **nguyên bản** từ gói `supplementaryFiles` của Europe PMC; hai ảnh `.webp` được chuyển sang `.jpg` **không crop, không đổi nội dung**.
- Ảnh ghép dùng `tools/make_composite.py` (letterbox nền đen, giữ tỉ lệ); attribution in trong dải đen từng ô.
- Không dùng tên tác giả cá nhân trong CREDITS vì chưa đối chiếu từng chuỗi tác giả; ghi **tạp chí + năm + PMCID** theo quy tắc trung thực nguồn.
